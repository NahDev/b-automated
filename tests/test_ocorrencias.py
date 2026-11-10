import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import buscar_ocorrencias  # noqa: E402


def _botao(linha):
    imagem = Image.new("RGB", (60, 30), (30, 90, 200))
    desenho = ImageDraw.Draw(imagem)
    desenho.rectangle((0, 0, 59, 29), outline=(0, 0, 0), width=2)
    desenho.line(linha, fill=(255, 255, 0), width=3)
    return imagem


@pytest.fixture
def cenario(tmp_path):
    print_alvo = _botao((10, 10, 50, 20))
    caminho = tmp_path / "botao.png"
    print_alvo.save(caminho)

    tela = Image.new("RGB", (400, 200), "white")
    tela.paste(print_alvo, (30, 30))
    tela.paste(print_alvo, (200, 120))
    # botao parecido, com a linha em outro lugar: nao deve contar como igual
    tela.paste(_botao((10, 20, 50, 10)), (300, 30))
    return tela, caminho


def test_encontra_todas_as_ocorrencias_iguais(cenario):
    tela, caminho = cenario

    ocorrencias, _ = buscar_ocorrencias(tela, caminho, confianca=0.95)

    posicoes = sorted((x, y) for x, y, _, _, _ in ocorrencias)
    assert posicoes == [(30, 30), (200, 120)]


def test_ocorrencias_vem_com_tamanho_e_confianca(cenario):
    tela, caminho = cenario

    ocorrencias, _ = buscar_ocorrencias(tela, caminho, confianca=0.95)

    for _, _, largura, altura, score in ocorrencias:
        assert (largura, altura) == (60, 30)
        assert score >= 0.95


def test_melhor_semelhanca_mesmo_abaixo_do_limite(cenario):
    tela, caminho = cenario
    so_parecido = Image.new("RGB", (400, 200), "white")
    so_parecido.paste(_botao((10, 20, 50, 10)), (300, 30))

    ocorrencias, melhor = buscar_ocorrencias(so_parecido, caminho, confianca=0.95)

    assert ocorrencias == []
    assert melhor is not None
    score, x, y, largura, altura = melhor
    assert score < 0.95
    assert abs(x - 300) <= 2 and abs(y - 30) <= 2


def test_sem_ocorrencia_quando_o_print_nao_existe_na_tela(tmp_path):
    caminho = tmp_path / "botao.png"
    _botao((10, 10, 50, 20)).save(caminho)
    tela = Image.new("RGB", (400, 200), "white")

    ocorrencias, _ = buscar_ocorrencias(tela, caminho, confianca=0.9)

    assert ocorrencias == []
