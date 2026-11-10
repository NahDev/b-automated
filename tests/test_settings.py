import json

from va.settings import Settings


def test_padroes_quando_nao_existe_arquivo(tmp_path):
    assert Settings.carregar(tmp_path / "nao_existe.json") == Settings()


def test_salvar_e_carregar_mantem_os_valores(tmp_path):
    caminho = tmp_path / "config.json"
    original = Settings(confianca=0.95, offset_x=-5, niveis_confianca_fallback=(0.9, 0.8))

    original.salvar(caminho)

    assert Settings.carregar(caminho) == original


def test_chaves_desconhecidas_sao_ignoradas(tmp_path):
    caminho = tmp_path / "config.json"
    caminho.write_text(json.dumps({"confianca": 0.9, "chave_antiga": "x"}), encoding="utf-8")

    settings = Settings.carregar(caminho)

    assert settings.confianca == 0.9
    assert settings.timeout == Settings().timeout


def test_alterar_nao_muda_a_instancia_original():
    original = Settings()

    novo = original.alterar(offset_x=7)

    assert original.offset_x == 0
    assert novo.offset_x == 7
