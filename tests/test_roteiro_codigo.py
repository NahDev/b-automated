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


def test_imagem_usa_a_constante_do_modulo_e_so_importa_o_necessario():
    resultado = codigo_roteiro([Passo("clicar_imagem", "login/botao_entrar.png")], "fluxo")

    assert "from src.template_constants import Login" in resultado.codigo
    assert 'return perform_action(Login.BOTAO_ENTRAR, acao="clicar", timeout=timeout)' not in resultado.codigo
    assert 'perform_action(Login.BOTAO_ENTRAR, acao="clicar", timeout=timeout)' in resultado.codigo
    assert "import pyautogui" not in resultado.codigo


def test_esperar_imagem_usa_acao_esperar():
    resultado = codigo_roteiro([Passo("esperar_imagem", "login/tela_inicial.png")], "fluxo")

    assert 'perform_action(Login.TELA_INICIAL, acao="esperar", timeout=timeout)' in resultado.codigo


def test_passos_de_ocr_ficam_de_fora_e_sao_listados():
    passos = [Passo("clicar_texto", "Salvar"), Passo("clicar_imagem", "login/botao_entrar.png")]

    resultado = codigo_roteiro(passos, "fluxo")

    assert resultado.nao_exportados == ("clicar_texto 'Salvar'",)
    assert "# nao exportado (depende do app): clicar_texto 'Salvar'" in resultado.codigo
    _parse(resultado.codigo)


def test_digitar_texto_com_acento_usa_a_area_de_transferencia():
    resultado = codigo_roteiro([Passo("digitar", "", "João")], "fluxo")

    assert "import pyperclip" in resultado.codigo
    assert "pyperclip.copy('João')" in resultado.codigo
    _parse(resultado.codigo)


def test_digitar_texto_simples_usa_pyautogui():
    resultado = codigo_roteiro([Passo("digitar", "usuario")], "fluxo")

    assert "pyautogui.write('usuario', interval=0.02)" in resultado.codigo


def test_tecla_com_combinacao_vira_hotkey():
    resultado = codigo_roteiro([Passo("tecla", "ctrl+shift+s")], "fluxo")

    assert "pyautogui.hotkey('ctrl', 'shift', 's')" in resultado.codigo


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
