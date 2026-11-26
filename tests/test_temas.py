import re

import pytest

from va.settings import Settings
from va.ui.temas import BTIME, NEUTRO, TEMAS, escolher_familia, obter

COR_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def test_padrao_e_o_tema_btime():
    assert Settings().tema == "btime"
    assert obter("btime") is BTIME


def test_nome_desconhecido_cai_no_tema_padrao():
    assert obter("inexistente") is BTIME


def test_todas_as_cores_sao_hexadecimais_validas():
    for tema in TEMAS.values():
        for campo in ("fundo", "superficie", "texto", "secundario", "borda", "primaria",
                      "texto_primaria", "ativo", "sucesso", "perigo", "visual"):
            assert COR_HEX.match(getattr(tema, campo)), f"{tema.nome}.{campo}"


def test_tokens_do_btime_vem_do_design_system():
    assert BTIME.fundo == "#F7F6FB"
    assert BTIME.primaria == "#571EE6"
    assert BTIME.visual == "#060315"


def test_temas_sao_os_esperados():
    assert set(TEMAS) == {"btime", "neutro"}
    assert NEUTRO.primaria == "#2563EB"


@pytest.mark.parametrize(
    ("candidatas", "disponiveis", "esperado"),
    [
        (("Branding Semilight", "Branding", "Segoe UI"), {"Segoe UI", "Branding"}, "Branding"),
        (("Branding Semilight", "Branding", "Segoe UI"), {"Segoe UI"}, "Segoe UI"),
        (("Branding Semilight", "Branding", "Segoe UI"), {"Branding Semilight", "Segoe UI"}, "Branding Semilight"),
        (("Segoe UI Semibold", "Segoe UI"), set(), "Segoe UI"),
    ],
)
def test_escolher_familia_pega_a_primeira_instalada(candidatas, disponiveis, esperado):
    assert escolher_familia(candidatas, disponiveis) == esperado
