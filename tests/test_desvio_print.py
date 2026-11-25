from PIL import Image

from va.biblioteca import Biblioteca
from va.export.storage import ler_acoes, ler_metadados
from va.export.template import MODELO_PERFORM_ACTION
from va.settings import Settings


def _biblioteca_com_dois_prints(tmp_path) -> Biblioteca:
    biblioteca = Biblioteca(tmp_path)
    biblioteca.salvar(Image.new("RGB", (20, 10), "blue"), "login", "botao", "clicar")
    biblioteca.salvar(Image.new("RGB", (20, 10), "green"), "login", "tela", "esperar")
    return biblioteca


def test_formato_antigo_do_acoes_json_ainda_e_lido(tmp_path):
    pasta = tmp_path / "login"
    pasta.mkdir()
    (pasta / "acoes.json").write_text('{"botao": "esperar"}', encoding="utf-8")

    assert ler_acoes(pasta) == {"botao": "esperar"}
    assert ler_metadados(pasta) == {"botao": {"acao": "esperar"}}


def test_desvio_do_print_e_salvo_e_removido(tmp_path):
    biblioteca = _biblioteca_com_dois_prints(tmp_path)

    assert biblioteca.desvio_do_print("login/botao.png") is None

    biblioteca.definir_desvio("login/botao.png", 12, -4)
    assert biblioteca.desvio_do_print("login/botao.png") == (12, -4)
    assert biblioteca.desvio_do_print("login/tela.png") is None

    biblioteca.definir_desvio("login/botao.png", None, None)
    assert biblioteca.desvio_do_print("login/botao.png") is None
    assert ler_acoes(tmp_path / "src" / "static" / "images" / "login") == {"botao": "clicar", "tela": "esperar"}


def test_codigo_gerado_leva_o_desvio_de_cada_print(tmp_path):
    biblioteca = _biblioteca_com_dois_prints(tmp_path)
    biblioteca.definir_desvio("login/botao.png", 12, -4)

    biblioteca.gerar_codigo(Settings())

    servico = (tmp_path / "src" / "services" / "login.py").read_text(encoding="utf-8")
    assert 'return perform_action(Login.BOTAO, acao="clicar", offset=(12, -4), timeout=timeout)' in servico
    assert 'return perform_action(Login.TELA, acao="esperar", timeout=timeout)' in servico


def test_perform_action_aceita_o_desvio_do_print():
    assert "offset=None" in MODELO_PERFORM_ACTION
    assert 'dx, dy = offset if offset is not None else (CONFIG_AUTOMACAO["offset_x"], CONFIG_AUTOMACAO["offset_y"])' in MODELO_PERFORM_ACTION
