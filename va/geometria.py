"""Geometria usada pelo laboratorio e pela medicao de desvio. Pura, sem interface: facil de testar."""

MARGEM_PADRAO = 80


def escala_para(largura: int, altura: int, canvas_w: int, canvas_h: int, margem: int = MARGEM_PADRAO) -> float:
    """Reduz o print so se ele nao couber no canvas com a margem. Nunca amplia."""
    cabe_w = (canvas_w - 2 * margem) / largura
    cabe_h = (canvas_h - 2 * margem) / altura
    return max(min(1.0, cabe_w, cabe_h), 0.01)


def desvio_do_clique(x: float, y: float, canvas_w: int, canvas_h: int, escala: float) -> tuple[int, int]:
    """Converte um ponto do canvas no desvio (dx, dy) em pixels reais, a partir do centro."""
    return round((x - canvas_w / 2) / escala), round((y - canvas_h / 2) / escala)


def ponto_no_canvas(dx: int, dy: int, canvas_w: int, canvas_h: int, escala: float) -> tuple[float, float]:
    return canvas_w / 2 + dx * escala, canvas_h / 2 + dy * escala


def desvio_entre(ponto_centro: tuple[int, int], ponto_alvo: tuple[int, int]) -> tuple[int, int]:
    """Desvio (dx, dy) do ponto alvo em relacao ao centro da referencia."""
    return ponto_alvo[0] - ponto_centro[0], ponto_alvo[1] - ponto_centro[1]
