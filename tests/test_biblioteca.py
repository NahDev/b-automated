from PIL import Image

from va.biblioteca import Biblioteca
from va.export.storage import ler_acoes


def test_salvar_cria_o_print_e_a_acao_padrao(tmp_path):
    biblioteca = Biblioteca(tmp_path)

    destino = biblioteca.salvar(Image.new("RGB", (20, 10), "blue"), "login", "botao", "esperar")

    assert destino.exists()
    assert biblioteca.nomes() == ["login/botao.png"]
    assert biblioteca.existe("login", "botao")
    assert ler_acoes(destino.parent) == {"botao": "esperar"}


def test_excluir_remove_o_print_e_a_acao(tmp_path):
    biblioteca = Biblioteca(tmp_path)
    destino = biblioteca.salvar(Image.new("RGB", (20, 10), "blue"), "login", "botao", "clicar")

    biblioteca.excluir("login/botao.png")

    assert not destino.exists()
    assert ler_acoes(destino.parent) == {}
    assert biblioteca.nomes() == []
