import ast

import pytest

from va.automation.runner import Passo
from va.export.roteiro import codigo_roteiro


def _parse(codigo: str) -> ast.Module:
    return ast.parse(codigo)


def test_codigo_gerado_tem_sintaxe_valida():
    passos = [
        Passo("clicar_imagem", "login/botao_entrar.png"),
        Passo("digitar", "", "usuario"),
        Passo("tecla", "ctrl+s"),
        Passo("esperar_segundos", "", "1.5"),
        Passo("esperar_imagem", "login/tela_inicial.png"),
    ]

    resultado = codigo_roteiro(passos, "fluxo_login")

    _parse(resultado.codigo)
    assert resultado.nao_exportados == ()


def test_clique_em_imagem_usa_a_pagina_e_a_api_do_projeto():
    resultado = codigo_roteiro([Passo("clicar_imagem", "login/botao_entrar.png")], "fluxo")

    assert "from src.configs.template_constants import LoginPage" in resultado.codigo
    assert "from src.libs.automation import ClickCommand, perform_action" in resultado.codigo
    assert "perform_action(template_name=LoginPage.BOTAO_ENTRAR, command=ClickCommand())" in resultado.codigo


def test_clique_com_desvio_proprio_usa_click_offset():
    resultado = codigo_roteiro(
        [Passo("clicar_imagem", "login/botao_entrar.png")],
        "fluxo",
        {"login/botao_entrar.png": (12, -4)},
    )

    assert "command=ClickOffsetCommand(dx=12, dy=-4)" in resultado.codigo
    assert "ClickCommand()" not in resultado.codigo


def test_esperar_imagem_levanta_erro_se_nao_aparecer():
    resultado = codigo_roteiro([Passo("esperar_imagem", "login/tela_inicial.png")], "fluxo")

    assert "if not find_element(template_path=LoginPage.TELA_INICIAL):" in resultado.codigo
    assert "raise ElementNotFound('Imagem nao apareceu: login/tela_inicial.png')" in resultado.codigo
    assert "from src.exceptions.exceptions import ElementNotFound" in resultado.codigo
    _parse(resultado.codigo)


def test_passos_de_ocr_ficam_de_fora_e_sao_listados():
    passos = [Passo("clicar_texto", "Salvar"), Passo("clicar_imagem", "login/botao_entrar.png")]

    resultado = codigo_roteiro(passos, "fluxo")

    assert resultado.nao_exportados == ("clicar_texto 'Salvar'",)
    assert "# nao exportado (depende do app): clicar_texto 'Salvar'" in resultado.codigo
    _parse(resultado.codigo)


def test_digitar_usa_writer_que_aceita_acentos():
    resultado = codigo_roteiro([Passo("digitar", "", "João")], "fluxo")

    assert "from src.libs.automation import writer" in resultado.codigo
    assert "writer('João')" in resultado.codigo
    _parse(resultado.codigo)


def test_tecla_simples_usa_press_key():
    resultado = codigo_roteiro([Passo("tecla", "enter")], "fluxo")

    assert "press_key('enter')" in resultado.codigo


def test_combinacao_de_teclas_usa_hotkey():
    resultado = codigo_roteiro([Passo("tecla", "ctrl+shift+s")], "fluxo")

    assert "pyautogui.hotkey('ctrl', 'shift', 's')" in resultado.codigo
    assert "import pyautogui" in resultado.codigo


def test_espera_invalida_nao_e_exportada():
    resultado = codigo_roteiro([Passo("esperar_segundos", "", "dois")], "fluxo")

    assert resultado.nao_exportados == ("esperar_segundos '' valor 'dois'",)


def test_roteiro_vazio_gera_funcao_com_pass():
    resultado = codigo_roteiro([], "vazio")

    assert "def roteiro_vazio(timeout=None):" in resultado.codigo
    assert "    pass" in resultado.codigo
    _parse(resultado.codigo)


def test_nome_invalido_levanta_erro():
    with pytest.raises(ValueError):
        codigo_roteiro([], "!!")
