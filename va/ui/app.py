"""Janela principal: junta as abas e coordena os servicos (configuracoes, biblioteca e automacao).

Quem muda uma configuracao chama `aplicar_settings`: ele persiste, recria os servicos que dependem
dela e atualiza as telas. As abas nao guardam configuracao propria.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from va.automation.actions import Automador
from va.biblioteca import Biblioteca
from va.logs import ARQUIVO_LOG
from va.logs import configurar as configurar_registro
from va.logs import logger
from va.settings import Settings
from va.ui.capture_tab import CapturaTab
from va.ui.dpi import ativar_dpi
from va.ui.lab_tab import AbaLaboratorio
from va.ui.overlay import medir_desvio
from va.ui.script_tab import RoteiroTab
from va.ui.settings_tab import ConfigTab


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Visual Automator")
        self.geometry("1000x680")
        self.minsize(860, 560)

        self.settings = Settings.carregar()
        self.automador = Automador(self.settings)
        self.biblioteca = Biblioteca(self.automador.pasta_saida)

        self.bind("<F9>", lambda _evento: self.captura.capturar())

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.captura = CapturaTab(notebook, self)
        self.roteiro = RoteiroTab(notebook, self)
        self.configuracoes = ConfigTab(notebook, self)
        self.laboratorio = AbaLaboratorio(notebook, self)
        notebook.add(self.captura, text="Capturar")
        notebook.add(self.roteiro, text="Roteiro")
        notebook.add(self.configuracoes, text="Configuracoes")
        notebook.add(self.laboratorio, text="Laboratorio")
        self.captura.atualizar_lista()

    def aplicar_settings(self, novo: Settings) -> None:
        """Persiste as configuracoes e recria o que depende delas."""
        novo.salvar()
        self.settings = novo
        self.automador = Automador(novo)
        self.biblioteca = Biblioteca(self.automador.pasta_saida)
        self.configuracoes.mostrar(novo)
        self.captura.atualizar_lista()
        self.laboratorio.mostrar_atual()
        self.gerar_codigo()

    def salvar_confianca_padrao(self, confianca: float) -> None:
        self.aplicar_settings(self.settings.alterar(confianca=confianca))
        self.registrar(f"Confianca padrao salva: {confianca:.2f}")

    def salvar_desvio_padrao(self, dx: int, dy: int) -> None:
        self.aplicar_settings(self.settings.alterar(offset_x=dx, offset_y=dy))
        self.registrar(f"Desvio padrao salvo: dx={dx}, dy={dy}")

    def gerar_codigo(self) -> None:
        try:
            self.biblioteca.gerar_codigo(self.settings)
        except OSError as erro:
            self.registrar(f"Falha ao gerar o codigo: {erro}")

    def medir_na_tela(self, ao_concluir: Callable[[int, int], None]) -> None:
        """Esconde o app e mede um desvio com dois cliques na tela congelada."""
        self.withdraw()
        self.after(300, lambda: medir_desvio(self, lambda desvio: self._fim_medicao(desvio, ao_concluir)))

    def registrar(self, mensagem: str) -> None:
        self.roteiro.log(mensagem)

    def report_callback_exception(self, exc, val, tb) -> None:
        """Erros de botoes e eventos da interface caem aqui: registra e avisa o usuario."""
        logger.error("Erro na interface", exc_info=(exc, val, tb))
        messagebox.showerror("Erro", f"{val}\n\nDetalhes em:\n{ARQUIVO_LOG}", parent=self)

    def _fim_medicao(self, desvio, ao_concluir) -> None:
        self.deiconify()
        if desvio is not None:
            ao_concluir(*desvio)


def main() -> None:
    ativar_dpi()
    configurar_registro()
    logger.info("Visual Automator iniciado")
    App().mainloop()
