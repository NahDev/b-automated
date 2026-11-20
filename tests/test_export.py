import ast

import pytest
from PIL import Image

from va.export.generator import gerar_codigo, trecho_constantes
from va.export.naming import identificador, identificador_modulo, nome_classe
from va.export.storage import gravar_acao
from va.settings import Settings


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


def _criar_pasta_de_prints(raiz):
    pasta = raiz / "src" / "static" / "images" / "login"
    pasta.mkdir(parents=True)
    Image.new("RGB", (20, 10), "blue").save(pasta / "botao_entrar.png")
    Image.new("RGB", (20, 10), "green").save(pasta / "tela_inicial.png")
    gravar_acao(pasta, "botao_entrar", "clicar")
    gravar_acao(pasta, "tela_inicial", "esperar")


def test_gera_constantes_e_automacao(tmp_path):
    _criar_pasta_de_prints(tmp_path)

    gerar_codigo(tmp_path, Settings())

    constantes = (tmp_path / "src" / "template_constants.py").read_text(encoding="utf-8")
    assert "class Login:" in constantes
    assert 'BOTAO_ENTRAR = "src/static/images/login/botao_entrar.png"' in constantes

    automacao = (tmp_path / "src" / "services" / "login.py").read_text(encoding="utf-8")
    assert "from src.template_constants import Login" in automacao
    assert "def clicar_botao_entrar(timeout=None):" in automacao
    assert "def esperar_tela_inicial(timeout=None):" in automacao
    assert 'return perform_action(Login.BOTAO_ENTRAR, acao="clicar", timeout=timeout)' in automacao


def test_guia_de_integracao_lista_arquivos_e_funcoes(tmp_path):
    _criar_pasta_de_prints(tmp_path)

    gerar_codigo(tmp_path, Settings())

    guia = (tmp_path / "INTEGRACAO.md").read_text(encoding="utf-8")
    assert "`src/services/login.py`" in guia
    assert "`clicar_botao_entrar(timeout=None)`" in guia
    assert "from src.services.login import clicar_botao_entrar" in guia


def test_trecho_do_modulo_traz_so_a_propria_classe():
    trecho = trecho_constantes("login", ["botao_entrar"])
    outro = trecho_constantes("pagamento", ["cartao"])

    assert trecho.startswith("class Login:")
    assert "BOTAO_ENTRAR" in trecho
    assert "class Pagamento" not in trecho
    assert outro.startswith("class Pagamento:")


def test_codigo_gerado_tem_sintaxe_valida(tmp_path):
    _criar_pasta_de_prints(tmp_path)

    gerar_codigo(tmp_path, Settings())

    arquivos = list((tmp_path / "src").rglob("*.py"))
    assert arquivos
    for arquivo in arquivos:
        ast.parse(arquivo.read_text(encoding="utf-8"), filename=str(arquivo))


def test_config_gerada_usa_valores_do_app(tmp_path):
    _criar_pasta_de_prints(tmp_path)

    gerar_codigo(tmp_path, Settings(confianca=0.91, offset_x=-4))

    config = (tmp_path / "src" / "automation" / "config.py").read_text(encoding="utf-8")
    assert "'confianca': 0.91," in config
    assert "'offset_x': -4," in config
