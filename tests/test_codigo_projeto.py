import ast

from PIL import Image

from va.biblioteca import Biblioteca
from va.export.generator import codigo_servico, trecho_constantes
from va.export.naming import classe_pagina, classe_servico, identificador, identificador_modulo


def _biblioteca(tmp_path) -> Biblioteca:
    biblioteca = Biblioteca(tmp_path)
    biblioteca.salvar(Image.new("RGB", (20, 10), "blue"), "login", "botao_entrar", "clicar")
    biblioteca.salvar(Image.new("RGB", (20, 10), "green"), "login", "tela_inicial", "esperar")
    return biblioteca


def test_nomes_seguem_o_padrao_do_projeto():
    assert classe_pagina("check_order") == "CheckOrderPage"
    assert classe_servico("check_order") == "CheckOrderService"
    assert identificador("Botão Entrar!") == "botao_entrar"
    assert identificador_modulo("config") == "config_pagina"


def test_servico_segue_o_padrao_dos_services_do_projeto(tmp_path):
    biblioteca = _biblioteca(tmp_path)

    biblioteca.gerar_codigo()

    servico = (tmp_path / "src" / "services" / "login.py").read_text(encoding="utf-8")
    ast.parse(servico)
    assert "from src.configs.template_constants import LoginPage" in servico
    assert "from src.libs.automation import ClickCommand, find_element, perform_action" in servico
    assert "class LoginService:" in servico
    assert "    def clicar_botao_entrar(self):" in servico
    assert "        perform_action(template_name=LoginPage.BOTAO_ENTRAR, command=ClickCommand())" in servico
    assert "    def esperar_tela_inicial(self, max_attempts=10):" in servico
    assert "        return find_element(template_path=LoginPage.TELA_INICIAL, max_attempts=max_attempts)" in servico


def test_desvio_do_print_vira_click_offset(tmp_path):
    biblioteca = _biblioteca(tmp_path)
    biblioteca.definir_desvio("login/botao_entrar.png", 12, -4)

    biblioteca.gerar_codigo()

    servico = (tmp_path / "src" / "services" / "login.py").read_text(encoding="utf-8")
    ast.parse(servico)
    assert "command=ClickOffsetCommand(dx=12, dy=-4))" in servico
    assert "from src.libs.automation import ClickOffsetCommand, find_element, perform_action" in servico
    assert "ClickCommand" not in servico


def test_trecho_da_pagina_herda_base_paths():
    trecho = trecho_constantes("check_order", ["button_alta"])

    ast.parse(trecho)
    assert trecho.startswith("class CheckOrderPage(_BasePaths):")
    assert '    BUTTON_ALTA = _BasePaths.BASE_DIR / "check_order" / "button_alta.png"' in trecho


def test_codigo_do_servico_nao_depende_de_outros_modulos():
    servico = codigo_servico("login", ["botao_entrar"], {})

    assert "CheckOrderPage" not in servico
    assert "from src.configs.template_constants import LoginPage" in servico


def test_guia_traz_o_trecho_e_o_passo_a_passo(tmp_path):
    biblioteca = _biblioteca(tmp_path)

    biblioteca.gerar_codigo()

    guia = (tmp_path / "INTEGRACAO.md").read_text(encoding="utf-8")
    assert "class LoginPage(_BasePaths):" in guia
    assert "src/services/login.py" in guia
    assert "template_constants.py" in guia
