from PIL import Image

from va.biblioteca import Biblioteca
from va.export.generator import GUIA
from va.export.storage import ler_acoes
from va.settings import Settings


def test_salvar_cria_o_print_e_a_acao_padrao(tmp_path):
    biblioteca = Biblioteca(tmp_path)

    destino = biblioteca.salvar(Image.new("RGB", (20, 10), "blue"), "login", "botao", "esperar")

    assert destino.exists()
    assert biblioteca.nomes() == ["login/botao.png"]
    assert biblioteca.existe("login", "botao")
    assert ler_acoes(destino.parent) == {"botao": "esperar"}


def test_exportar_copia_src_e_o_guia_para_o_projeto(tmp_path):
    biblioteca = Biblioteca(tmp_path / "saida")
    biblioteca.salvar(Image.new("RGB", (20, 10), "blue"), "login", "botao", "clicar")
    biblioteca.gerar_codigo(Settings())
    projeto = tmp_path / "meu_projeto"
    projeto.mkdir()

    src = biblioteca.exportar(projeto)

    assert (src / "services" / "login.py").exists()
    assert (src / "static" / "images" / "login" / "botao.png").exists()
    assert (projeto / GUIA).exists()


def test_codigo_do_modulo_devolve_trecho_e_arquivo(tmp_path):
    biblioteca = Biblioteca(tmp_path)
    biblioteca.salvar(Image.new("RGB", (20, 10), "blue"), "login", "botao", "clicar")

    trecho, arquivo = biblioteca.codigo_do_modulo("login")

    assert "BOTAO = " in trecho
    assert "def clicar_botao(timeout=None):" in arquivo


def test_excluir_remove_o_print_e_a_acao(tmp_path):
    biblioteca = Biblioteca(tmp_path)
    destino = biblioteca.salvar(Image.new("RGB", (20, 10), "blue"), "login", "botao", "clicar")

    biblioteca.excluir("login/botao.png")

    assert not destino.exists()
    assert ler_acoes(destino.parent) == {}
    assert biblioteca.nomes() == []
