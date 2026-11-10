"""Escala do Windows (DPI)."""

import ctypes


def ativar_dpi() -> None:
    """Sem isso, com escala de 125% ou 150% as coordenadas do print e do clique nao batem."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        pass
