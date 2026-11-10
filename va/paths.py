"""Pastas do programa. Funciona igual no codigo-fonte e no executavel (PyInstaller)."""

import sys
from pathlib import Path

# Codigo-fonte: raiz do projeto. Executavel: pasta onde esta o .exe.
BASE_DIR = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parents[1]
)


def pasta_imagens(pasta_saida: Path) -> Path:
    """Onde ficam os prints, organizados por modulo (pagina)."""
    return pasta_saida / "src" / "static" / "images"
