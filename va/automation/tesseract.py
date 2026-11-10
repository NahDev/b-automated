"""Localizacao do Tesseract e dos idiomas usados pelo OCR."""

import os
from pathlib import Path

import pytesseract

from va.paths import BASE_DIR
from va.settings import Settings

TESSERACT_PADRAO = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")


def localizar_tesseract(configurado: str) -> str | None:
    """Ordem: caminho configurado (se existir), Tesseract empacotado, instalacao padrao do Windows."""
    if configurado and Path(configurado).exists():
        return configurado
    for caminho in (BASE_DIR / "tesseract" / "tesseract.exe", TESSERACT_PADRAO):
        if caminho.exists():
            return str(caminho)
    return configurado or None


def configurar_ocr(settings: Settings) -> None:
    caminho = localizar_tesseract(settings.tesseract_cmd)
    if caminho:
        pytesseract.pytesseract.tesseract_cmd = caminho
    pasta_tessdata = BASE_DIR / settings.pasta_tessdata
    if pasta_tessdata.is_dir():
        # Usa os idiomas do projeto (ex: por.traineddata) em vez dos da pasta do Tesseract
        os.environ["TESSDATA_PREFIX"] = str(pasta_tessdata)
