"""Modelo do modulo perform_action.py que vai junto com o codigo exportado para o projeto do usuario."""

MODELO_PERFORM_ACTION = '''"""Executa uma acao visual: acha a imagem na tela e age sobre ela.

Gerado pelo Visual Automator. Os padroes ficam em src/automation/config.py.
"""

import time
from pathlib import Path

import pyautogui
import pyscreeze

from src.automation.config import CONFIG_AUTOMACAO

RAIZ = Path(__file__).resolve().parents[2]
ACOES = ("clicar", "clicar_duplo", "clicar_direito", "esperar")

pyautogui.FAILSAFE = True  # mouse no canto superior esquerdo aborta


class ImagemNaoEncontrada(Exception):
    pass


def _localizar(caminho, regiao=None, confianca=None):
    nivel = CONFIG_AUTOMACAO["confianca"] if confianca is None else confianca
    niveis = [nivel, *CONFIG_AUTOMACAO["niveis_confianca_fallback"]]
    tela = pyautogui.screenshot(region=regiao)
    for valor in niveis:
        try:
            caixa = pyscreeze.locate(caminho, tela, confidence=valor, grayscale=CONFIG_AUTOMACAO["escala_cinza"])
        except pyscreeze.ImageNotFoundException:
            caixa = None
        if caixa is not None:
            x, y, largura, altura = (int(valor_caixa) for valor_caixa in caixa)
            if regiao is not None:
                x, y = x + regiao[0], y + regiao[1]
            return x, y, largura, altura
    return None


def perform_action(imagem, acao="clicar", timeout=None, regiao=None, confianca=None):
    """Localiza `imagem` (caminho relativo a raiz do projeto) e executa `acao`.

    Retorna o ponto (x, y) clicado, ou a caixa encontrada quando a acao e "esperar".
    Levanta ImagemNaoEncontrada se a imagem nao aparecer dentro do timeout.
    """
    if acao not in ACOES:
        raise ValueError(f"Acao desconhecida: {acao}")
    caminho = Path(imagem)
    if not caminho.is_absolute():
        caminho = RAIZ / caminho
    limite = time.monotonic() + (CONFIG_AUTOMACAO["timeout"] if timeout is None else timeout)
    caixa = _localizar(str(caminho), regiao, confianca)
    while caixa is None and time.monotonic() < limite:
        time.sleep(CONFIG_AUTOMACAO["intervalo"])
        caixa = _localizar(str(caminho), regiao, confianca)
    if caixa is None:
        raise ImagemNaoEncontrada(f"Imagem nao encontrada: {imagem}")
    if acao == "esperar":
        return caixa
    x = caixa[0] + caixa[2] // 2 + CONFIG_AUTOMACAO["offset_x"]
    y = caixa[1] + caixa[3] // 2 + CONFIG_AUTOMACAO["offset_y"]
    pyautogui.moveTo(x, y, duration=CONFIG_AUTOMACAO["duracao_movimento"])
    if acao == "clicar_duplo":
        pyautogui.doubleClick(x, y)
    elif acao == "clicar_direito":
        pyautogui.click(x, y, button="right")
    else:
        pyautogui.click(x, y)
    time.sleep(CONFIG_AUTOMACAO["pausa_entre_passos"])
    return x, y
'''
