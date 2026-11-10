"""Registro em arquivo: grava erros e resultados dos passos em logs/visual_automator.log.

Util quando o programa roda como .exe, sem console, para descobrir o que aconteceu.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

from config import BASE_DIR

ARQUIVO_LOG = BASE_DIR / "logs" / "visual_automator.log"
logger = logging.getLogger("visual_automator")


def configurar() -> None:
    ARQUIVO_LOG.parent.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = RotatingFileHandler(ARQUIVO_LOG, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)

    def _erro_nao_tratado(tipo, valor, tb):
        logger.error("Erro nao tratado", exc_info=(tipo, valor, tb))

    sys.excepthook = _erro_nao_tratado
