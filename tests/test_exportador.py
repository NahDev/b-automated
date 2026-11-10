import ast
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import PADROES  # noqa: E402
from exportador import (  # noqa: E402
    gerar_codigo,
    gravar_acao,
    identificador,
    identificador_modulo,
    nome_classe,
)


def test_identificador_remove_acentos_e_simbolos():
    assert identificador("Botão Entrar!") == "botao_entrar"


def test_identificador_trata_numero_inicial_e_palavra_reservada():
    assert identificador("1 tela") == "p_1_tela"
    assert identificador("class") == "class_"


def test_identificador_vazio_levanta_erro():
    with pytest.raises(ValueError):
        identificador("  !!  ")


def test_identificador_modulo_evita_nomes_reservados():
    assert identificador_modulo("config") == "config_pagina"


def test_nome_classe_em_camel_case():
    assert nome_classe("tela_de_login") == "TelaDeLogin"


def _criar_pasta_de_prints(raiz: Path) -> None:
    pasta = raiz / "src" / "static" / "images" / "login"
    pasta.mkdir(parents=True)
    Image.new("RGB", (20, 10), "blue").save(pasta / "botao_entrar.png")
    Image.new("RGB", (20, 10), "green").save(pasta / "tela_inicial.png")
    gravar_acao(pasta, "botao_entrar", "clicar")
    gravar_acao(pasta, "tela_inicial", "esperar")


def test_gera_constantes_e_automacao(tmp_path):
    _criar_pasta_de_prints(tmp_path)

    gerar_codigo(tmp_path, dict(PADROES))

    constantes = (tmp_path / "src" / "template_constants.py").read_text(encoding="utf-8")
    assert "class Login:" in constantes
    assert 'return "src/static/images/login/botao_entrar.png"' in constantes

    automacao = (tmp_path / "src" / "services" / "login.py").read_text(encoding="utf-8")
    assert "def clicar_botao_entrar(timeout=None):" in automacao
    assert "def esperar_tela_inicial(timeout=None):" in automacao
    assert 'perform_action(Login.botao_entrar(), acao="clicar", timeout=timeout)' in automacao


def test_codigo_gerado_tem_sintaxe_valida(tmp_path):
    _criar_pasta_de_prints(tmp_path)

    gerar_codigo(tmp_path, dict(PADROES))

    arquivos = list((tmp_path / "src").rglob("*.py"))
    assert arquivos
    for arquivo in arquivos:
        ast.parse(arquivo.read_text(encoding="utf-8"), filename=str(arquivo))


def test_config_gerada_usa_valores_do_app(tmp_path):
    _criar_pasta_de_prints(tmp_path)

    gerar_codigo(tmp_path, dict(PADROES, confianca=0.91, offset_x=-4))

    config = (tmp_path / "src" / "automation" / "config.py").read_text(encoding="utf-8")
    assert "'confianca': 0.91," in config
    assert "'offset_x': -4," in config
