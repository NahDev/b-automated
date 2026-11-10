"""Acoes de automacao no estilo SikuliX: achar por imagem ou por texto (OCR), clicar e digitar."""

import os
import time
from pathlib import Path

import cv2
import numpy as np
import pyautogui
import pyperclip
import pyscreeze
import pytesseract
from PIL import Image

from config import BASE_DIR, carregar
from exportador import pasta_imagens

pyautogui.FAILSAFE = True  # mouse no canto superior esquerdo aborta a automacao
pyautogui.PAUSE = 0.05

Caixa = tuple[int, int, int, int]  # (left, top, width, height)

ACOES = [
    "clicar_imagem",
    "esperar_imagem",
    "clicar_texto",
    "esperar_texto",
    "digitar",
    "tecla",
    "esperar_segundos",
]


TESSERACT_PADRAO = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")


def _tesseract_padrao() -> str | None:
    """Tesseract empacotado ao lado do programa, ou instalado na pasta padrao do Windows."""
    for caminho in (BASE_DIR / "tesseract" / "tesseract.exe", TESSERACT_PADRAO):
        if caminho.exists():
            return str(caminho)
    return None


class ElementoNaoEncontrado(Exception):
    pass


class Automador:
    def __init__(self, config: dict | None = None):
        self.config = config or carregar()
        tesseract = self.config["tesseract_cmd"]
        if not (tesseract and Path(tesseract).exists()):
            tesseract = _tesseract_padrao() or tesseract
        if tesseract:
            pytesseract.pytesseract.tesseract_cmd = tesseract
        pasta_tessdata = BASE_DIR / self.config["pasta_tessdata"]
        if pasta_tessdata.is_dir():
            # Usa os idiomas do projeto (ex: por.traineddata) em vez da pasta do Tesseract
            os.environ["TESSDATA_PREFIX"] = str(pasta_tessdata)
        self.pasta_saida = BASE_DIR / self.config["pasta_saida"]
        self.pasta_imagens = pasta_imagens(self.pasta_saida)

    def caminho_imagem(self, nome: str) -> Path:
        caminho = Path(nome)
        if caminho.is_absolute() or caminho.exists():
            return caminho
        return self.pasta_imagens / nome

    def localizar_imagem(self, imagem: str, regiao: Caixa | None = None, confianca: float | None = None) -> Caixa | None:
        """Procura a imagem na tela agora, tentando os niveis de confianca em ordem."""
        caminho = str(self.caminho_imagem(imagem))
        nivel = self.config["confianca"] if confianca is None else confianca
        niveis = [nivel, *self.config["niveis_confianca_fallback"]]
        tela = pyautogui.screenshot(region=regiao)
        for confianca_atual in niveis:
            try:
                caixa = pyscreeze.locate(
                    caminho, tela, confidence=confianca_atual, grayscale=self.config["escala_cinza"]
                )
            except pyscreeze.ImageNotFoundException:
                caixa = None
            if caixa is not None:
                return self._somar_regiao(tuple(int(valor) for valor in caixa), regiao)
        return None

    def localizar_texto(self, texto: str, regiao: Caixa | None = None, timeout: float | None = None) -> Caixa | None:
        return self._esperar(lambda: self._buscar_texto(texto, regiao), timeout)

    def esperar_imagem(self, imagem: str, timeout: float | None = None, regiao: Caixa | None = None) -> Caixa | None:
        return self._esperar(lambda: self.localizar_imagem(imagem, regiao), timeout)

    def clicar_centro(self, caixa: Caixa, botao: str = "left", cliques: int = 1) -> None:
        x = caixa[0] + caixa[2] // 2 + self.config["offset_x"]
        y = caixa[1] + caixa[3] // 2 + self.config["offset_y"]
        pyautogui.moveTo(x, y, duration=self.config["duracao_movimento"])
        pyautogui.click(x=x, y=y, clicks=cliques, button=botao)

    def digitar(self, texto: str) -> None:
        if texto.isascii():
            pyautogui.write(texto, interval=0.02)
        else:
            # pyautogui nao digita acentos; colar pela area de transferencia resolve
            pyperclip.copy(texto)
            pyautogui.hotkey("ctrl", "v")

    def executar(self, acao: str, alvo: str = "", valor: str = "", timeout: float | None = None) -> None:
        """Executa um passo do roteiro. Lanca ElementoNaoEncontrado se nao achar o alvo."""
        if acao == "clicar_imagem":
            caixa = self.esperar_imagem(alvo, timeout)
            if caixa is None:
                raise ElementoNaoEncontrado(f"Imagem nao encontrada: {alvo}")
            self.clicar_centro(caixa)
        elif acao == "esperar_imagem":
            if self.esperar_imagem(alvo, timeout) is None:
                raise ElementoNaoEncontrado(f"Imagem nao apareceu: {alvo}")
        elif acao == "clicar_texto":
            caixa = self.localizar_texto(alvo, timeout=timeout)
            if caixa is None:
                raise ElementoNaoEncontrado(f"Texto nao encontrado: {alvo}")
            self.clicar_centro(caixa)
        elif acao == "esperar_texto":
            if self.localizar_texto(alvo, timeout=timeout) is None:
                raise ElementoNaoEncontrado(f"Texto nao apareceu: {alvo}")
        elif acao == "digitar":
            self.digitar(valor or alvo)
        elif acao == "tecla":
            pyautogui.hotkey(*[parte.strip() for parte in alvo.split("+")])
        elif acao == "esperar_segundos":
            time.sleep(float(valor or alvo))
        else:
            raise ValueError(f"Acao desconhecida: {acao}")
        time.sleep(self.config["pausa_entre_passos"])

    def _esperar(self, buscar, timeout: float | None):
        limite = time.monotonic() + (self.config["timeout"] if timeout is None else timeout)
        while True:
            caixa = buscar()
            if caixa is not None:
                return caixa
            if time.monotonic() >= limite:
                return None
            time.sleep(self.config["intervalo"])

    def _buscar_texto(self, texto: str, regiao: Caixa | None) -> Caixa | None:
        """OCR da tela; casa sequencias de palavras (contem, sem diferenciar maiusculas)."""
        partes = texto.lower().split()
        if not partes:
            return None
        tela = pyautogui.screenshot(region=regiao)
        # psm 11 = texto esparso: acha palavras soltas na tela inteira (o modo padrao perde textos grandes entre outros elementos)
        dados = pytesseract.image_to_data(
            tela, lang=self.config["idioma_ocr"], config="--psm 11", output_type=pytesseract.Output.DICT
        )
        indices = [i for i, palavra in enumerate(dados["text"]) if palavra.strip()]
        for inicio in range(len(indices) - len(partes) + 1):
            trecho = indices[inicio:inicio + len(partes)]
            if all(parte in dados["text"][i].lower() for parte, i in zip(partes, trecho)):
                x0 = min(dados["left"][i] for i in trecho)
                y0 = min(dados["top"][i] for i in trecho)
                x1 = max(dados["left"][i] + dados["width"][i] for i in trecho)
                y1 = max(dados["top"][i] + dados["height"][i] for i in trecho)
                return self._somar_regiao((x0, y0, x1 - x0, y1 - y0), regiao)
        return None

    @staticmethod
    def _somar_regiao(caixa: Caixa, regiao: Caixa | None) -> Caixa:
        """Converte coordenadas relativas a regiao para coordenadas da tela."""
        if regiao is None:
            return caixa
        return (caixa[0] + regiao[0], caixa[1] + regiao[1], caixa[2], caixa[3])


def buscar_ocorrencias(
    tela: Image.Image, caminho: Path, confianca: float, escala_cinza: bool = True, limite: int = 50
) -> tuple[list[tuple[int, int, int, int, float]], tuple[float, int, int, int, int] | None]:
    """Acha todas as ocorrencias do print em `tela` com confianca >= `confianca`.

    Devolve (ocorrencias, melhor):
    - ocorrencias: [(x, y, largura, altura, confianca)], da mais parecida para a menos.
    - melhor: (confianca, x, y, largura, altura) da melhor semelhanca, mesmo abaixo do limite.
      None se o print nao couber na tela ou nao tiver variacao para comparar.
    """
    modo = "L" if escala_cinza else "RGB"
    imagem_tela = np.array(tela.convert(modo))
    alvo = np.array(Image.open(caminho).convert(modo))
    altura, largura = alvo.shape[:2]
    if altura > imagem_tela.shape[0] or largura > imagem_tela.shape[1] or alvo.std() == 0:
        return [], None

    res = cv2.matchTemplate(imagem_tela, alvo, cv2.TM_CCOEFF_NORMED)
    res = np.nan_to_num(res, nan=0.0, posinf=0.0, neginf=0.0)
    y_melhor, x_melhor = np.unravel_index(np.argmax(res), res.shape)
    melhor = (float(res[y_melhor, x_melhor]), int(x_melhor), int(y_melhor), largura, altura)

    ys, xs = np.where(res >= confianca)
    candidatos = sorted(zip(res[ys, xs].tolist(), xs.tolist(), ys.tolist()), reverse=True)
    escolhidos: list[tuple[int, int, float]] = []
    for score, x, y in candidatos:
        # Ignora posicoes que se sobrepoem a uma ocorrencia ja escolhida (mesmo botao)
        if all(abs(x - ex) >= largura / 2 or abs(y - ey) >= altura / 2 for ex, ey, _ in escolhidos):
            escolhidos.append((x, y, score))
            if len(escolhidos) == limite:
                break
    return [(x, y, largura, altura, score) for x, y, score in escolhidos], melhor
