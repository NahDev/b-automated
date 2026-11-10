"""Configuracoes padrao do visual_automator, salvas em config.json."""

import json
import sys
from pathlib import Path

# Quando empacotado com PyInstaller, a pasta do programa e a pasta do .exe
BASE_DIR = (
    Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
)
ARQUIVO_CONFIG = BASE_DIR / "config.json"

PADROES = {
    "confianca": 0.8,
    "niveis_confianca_fallback": [0.7, 0.6],
    "timeout": 10.0,
    "intervalo": 0.5,
    "escala_cinza": True,
    "duracao_movimento": 0.2,
    "offset_x": 0,
    "offset_y": 0,
    "pausa_entre_passos": 0.3,
    "pasta_saida": "saida",
    "pasta_tessdata": "tessdata",
    "idioma_ocr": "por+eng",
    "tesseract_cmd": "",
}


def carregar(caminho: Path = ARQUIVO_CONFIG) -> dict:
    """Le config.json e completa com os padroes o que estiver faltando."""
    config = dict(PADROES)
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        config.update({chave: valor for chave, valor in dados.items() if chave in PADROES})
    except (OSError, json.JSONDecodeError):
        pass
    return config


def salvar(config: dict, caminho: Path = ARQUIVO_CONFIG) -> None:
    dados = {chave: config[chave] for chave in PADROES}
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=2, ensure_ascii=False)
