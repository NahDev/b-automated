import time

from va.automation.actions import ElementoNaoEncontrado
from va.automation.runner import Passo, Runner


def _esperar_fim(runner: Runner) -> None:
    while runner.ocupado:
        time.sleep(0.01)


def test_executa_todos_os_passos_em_ordem():
    executados = []
    registros = []
    runner = Runner(lambda passo: executados.append(passo.acao))

    assert runner.iniciar([Passo("a", "x"), Passo("b", "y")], registros.append)
    _esperar_fim(runner)

    assert executados == ["a", "b"]
    assert registros == ["--- Inicio ---", "1. OK: a x", "2. OK: b y", "--- Fim ---"]


def test_para_no_primeiro_passo_que_nao_acha_o_alvo():
    registros = []

    def executar(passo):
        if passo.alvo == "x":
            raise ElementoNaoEncontrado("nao achou")

    runner = Runner(executar)
    runner.iniciar([Passo("a", "x"), Passo("b", "y")], registros.append)
    _esperar_fim(runner)

    assert "1. FALHOU: nao achou" in registros
    assert not any(linha.startswith("2.") for linha in registros)


def test_parar_interrompe_antes_do_proximo_passo():
    registros = []
    executados = []
    runner = None

    def executar(passo):
        executados.append(passo.acao)
        runner.parar()

    runner = Runner(executar)
    runner.iniciar([Passo("a"), Passo("b")], registros.append)
    _esperar_fim(runner)

    assert executados == ["a"]
    assert "Parado pelo usuario." in registros


def test_roteiro_vazio_nao_inicia():
    runner = Runner(lambda passo: None)

    assert runner.iniciar([], lambda linha: None) is False
    assert not runner.ocupado


def test_passo_convertido_de_e_para_dict():
    passo = Passo("digitar", "", "olá")

    assert Passo.de_dict(passo.para_dict()) == passo
