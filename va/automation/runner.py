"""Execucao de roteiros: roda os passos em ordem, em outra thread, com parada e registro."""

import threading
from dataclasses import dataclass
from typing import Callable

import pyautogui

from va.automation.actions import ElementoNaoEncontrado
from va.logs import logger


@dataclass(frozen=True)
class Passo:
    acao: str
    alvo: str = ""
    valor: str = ""

    @classmethod
    def de_dict(cls, dados: dict) -> "Passo":
        return cls(dados["acao"], dados.get("alvo", ""), dados.get("valor", ""))

    def para_dict(self) -> dict:
        return {"acao": self.acao, "alvo": self.alvo, "valor": self.valor}


class Runner:
    """Roda uma lista de passos sem bloquear a interface.

    `executar_passo` faz o trabalho de um passo e levanta excecao se ele falhar.
    `registrar` recebe as linhas de andamento; deve ser seguro para chamar de outra thread.
    """

    def __init__(self, executar_passo: Callable[[Passo], None]):
        self._executar_passo = executar_passo
        self._parar = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def ocupado(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def iniciar(self, passos: list[Passo], registrar: Callable[[str], None]) -> bool:
        if self.ocupado or not passos:
            return False
        self._parar.clear()
        self._thread = threading.Thread(target=self._rodar, args=(list(passos), registrar), daemon=True)
        self._thread.start()
        return True

    def parar(self) -> None:
        self._parar.set()

    def _rodar(self, passos: list[Passo], registrar: Callable[[str], None]) -> None:
        registrar("--- Inicio ---")
        for numero, passo in enumerate(passos, 1):
            if self._parar.is_set():
                registrar("Parado pelo usuario.")
                break
            try:
                self._executar_passo(passo)
            except ElementoNaoEncontrado as erro:
                registrar(f"{numero}. FALHOU: {erro}")
                logger.warning("Passo %d FALHOU: %s", numero, erro)
                break
            except pyautogui.FailSafeException:
                registrar("Interrompido: mouse no canto superior esquerdo (FailSafe).")
                logger.warning("Interrompido pelo FailSafe no passo %d", numero)
                break
            except Exception as erro:
                registrar(f"{numero}. ERRO: {erro}")
                logger.exception("Passo %d com erro", numero)
                break
            registrar(f"{numero}. OK: {passo.acao} {passo.alvo}")
            logger.info("Passo %d OK: %s %s", numero, passo.acao, passo.alvo)
        registrar("--- Fim ---")
