import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from captura import desvio_entre  # noqa: E402


def test_desvio_e_a_diferenca_entre_alvo_e_centro():
    assert desvio_entre((100, 200), (130, 190)) == (30, -10)


def test_desvio_zero_quando_os_cliques_coincidem():
    assert desvio_entre((50, 50), (50, 50)) == (0, 0)
