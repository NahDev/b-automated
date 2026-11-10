import shutil

import pyautogui
import pytest
from PIL import Image, ImageDraw, ImageFont

from va.automation.actions import Automador
from va.automation.tesseract import localizar_tesseract
from va.settings import Settings


def _tem_tesseract() -> bool:
    return localizar_tesseract("") is not None or shutil.which("tesseract") is not None


def _tela_com_botao() -> Image.Image:
    """Tela falsa 400x300 com um 'botao' desenhado em (120, 80), 60x30."""
    tela = Image.new("RGB", (400, 300), "white")
    desenho = ImageDraw.Draw(tela)
    desenho.rectangle((120, 80, 179, 109), fill=(30, 90, 200), outline=(0, 0, 0), width=2)
    desenho.line((130, 90, 170, 100), fill=(255, 255, 0), width=3)
    return tela


@pytest.fixture
def automador():
    return Automador(Settings(timeout=0, intervalo=0.01, pausa_entre_passos=0))


def test_localiza_imagem_na_tela(monkeypatch, tmp_path, automador):
    tela = _tela_com_botao()
    monkeypatch.setattr(pyautogui, "screenshot", lambda region=None: tela)
    alvo = tmp_path / "botao.png"
    tela.crop((120, 80, 180, 110)).save(alvo)

    caixa = automador.localizar_imagem(str(alvo))

    assert caixa is not None
    assert caixa[0] == pytest.approx(120, abs=2)
    assert caixa[1] == pytest.approx(80, abs=2)


def test_nao_encontra_imagem_ausente(monkeypatch, tmp_path, automador):
    monkeypatch.setattr(pyautogui, "screenshot", lambda region=None: _tela_com_botao())
    alvo = tmp_path / "listras.png"
    listras = Image.new("RGB", (60, 30), "white")
    desenho = ImageDraw.Draw(listras)
    for x in range(0, 60, 6):
        desenho.rectangle((x, 0, x + 2, 29), fill=(200, 0, 0))
    listras.save(alvo)

    assert automador.localizar_imagem(str(alvo)) is None


def test_regiao_soma_deslocamento(monkeypatch, tmp_path, automador):
    tela = _tela_com_botao()

    def captura(region=None):
        if region is None:
            return tela
        left, top, width, height = region
        return tela.crop((left, top, left + width, top + height))

    monkeypatch.setattr(pyautogui, "screenshot", captura)
    alvo = tmp_path / "botao.png"
    tela.crop((120, 80, 180, 110)).save(alvo)

    caixa = automador.localizar_imagem(str(alvo), regiao=(100, 60, 200, 100))

    assert caixa is not None
    assert caixa[0] == pytest.approx(120, abs=2)
    assert caixa[1] == pytest.approx(80, abs=2)


@pytest.mark.skipif(not _tem_tesseract(), reason="Tesseract nao instalado")
def test_localiza_texto_por_ocr(monkeypatch):
    tela = Image.new("RGB", (500, 150), "white")
    fonte = ImageFont.load_default(size=40)
    ImageDraw.Draw(tela).text((40, 40), "Salvar", fill="black", font=fonte)
    monkeypatch.setattr(pyautogui, "screenshot", lambda region=None: tela)
    automador = Automador(Settings(timeout=0, intervalo=0.01, idioma_ocr="eng"))

    caixa = automador.localizar_texto("Salvar")

    assert caixa is not None
    assert caixa[0] == pytest.approx(40, abs=10)
