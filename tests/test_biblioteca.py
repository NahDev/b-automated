import pytest
from PIL import Image

from va.biblioteca import Biblioteca
from va.export.storage import ler_acoes, ler_metadados


def _biblioteca(tmp_path) -> Biblioteca:
    biblioteca = Biblioteca(tmp_path / "saida")
    biblioteca.salvar(Image.new("RGB", (20, 10), "blue"), "login", "botao", "esperar")
    return biblioteca


def test_salvar_cria_o_print_e_a_acao_padrao(tmp_path):
    biblioteca = _biblioteca(tmp_path)

    assert biblioteca.nomes() == ["login/botao.png"]
    assert biblioteca.existe("login", "botao")
    assert ler_acoes(biblioteca.caminho("login/botao.png").parent) == {"botao": "esperar"}


def test_excluir_remove_o_print_e_a_acao(tmp_path):
    biblioteca = _biblioteca(tmp_path)

    biblioteca.excluir("login/botao.png")

    assert biblioteca.nomes() == []
    assert ler_acoes(biblioteca.pasta_imagens / "login") == {}


def test_formato_antigo_do_acoes_json_ainda_e_lido(tmp_path):
    pasta = tmp_path / "login"
    pasta.mkdir()
    (pasta / "acoes.json").write_text('{"botao": "esperar"}', encoding="utf-8")

    assert ler_metadados(pasta) == {"botao": {"acao": "esperar"}}


def test_desvio_do_print_e_salvo_e_removido(tmp_path):
    biblioteca = _biblioteca(tmp_path)

    assert biblioteca.desvio_do_print("login/botao.png") is None

    biblioteca.definir_desvio("login/botao.png", 12, -4)
    assert biblioteca.desvio_do_print("login/botao.png") == (12, -4)

    biblioteca.definir_desvio("login/botao.png", None, None)
    assert biblioteca.desvio_do_print("login/botao.png") is None
    assert ler_acoes(biblioteca.pasta_imagens / "login") == {"botao": "esperar"}


def test_exportar_copia_prints_e_servicos_sem_tocar_no_que_ja_existe(tmp_path):
    biblioteca = _biblioteca(tmp_path)
    biblioteca.gerar_codigo()
    projeto = tmp_path / "projeto"
    (projeto / "src" / "services").mkdir(parents=True)
    (projeto / "src" / "services" / "login.py").write_text("# servico existente\n", encoding="utf-8")

    resultado = biblioteca.exportar(projeto)

    assert "static/images/login/botao.png" in resultado.copiados
    assert (projeto / "src" / "static" / "images" / "login" / "botao.png").exists()
    assert resultado.ignorados == ("services/login.py",)
    assert (projeto / "src" / "services" / "login.py").read_text(encoding="utf-8") == "# servico existente\n"
    assert (projeto / "INTEGRACAO.md").exists()


def test_exportar_sem_codigo_gerado_avisa(tmp_path):
    biblioteca = Biblioteca(tmp_path / "saida_vazia")

    with pytest.raises(FileNotFoundError):
        biblioteca.exportar(tmp_path / "projeto")


def test_codigo_do_modulo_devolve_classe_e_servico(tmp_path):
    biblioteca = _biblioteca(tmp_path)

    trecho, servico = biblioteca.codigo_do_modulo("login")

    assert trecho.startswith("class LoginPage(_BasePaths):")
    assert "class LoginService:" in servico
    assert "def esperar_botao(self, max_attempts=10):" in servico
