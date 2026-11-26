"""Janela principal: junta as abas e coordena os servicos (configuracoes, biblioteca e automacao).

Quem muda uma configuracao chama `aplicar_settings`: ele persiste, recria os servicos que dependem
dela e atualiza as telas. As abas nao guardam configuracao propria.
"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from PIL import Image

from va.automation.actions import Automador
from va.biblioteca import Biblioteca
from va.logs import ARQUIVO_LOG
from va.logs import configurar as configurar_registro
from va.logs import logger
from va.settings import Settings
from va.ui.capture_tab import CapturaTab
from va.ui.dialogs import aviso_temporario, pedir_dados_print
from va.ui.dpi import ativar_dpi
from va.ui.lab_tab import AbaLaboratorio
from va.ui.overlay import medir_ancorado as abrir_medicao_ancorada
from va.ui.overlay import medir_desvio
from va.ui.script_tab import RoteiroTab
from va.ui.settings_tab import ConfigTab
from va.ui.temas import aplicar as aplicar_tema
from va.ui.temas import obter as obter_tema


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Visual Automator")
        self.geometry("1000x680")
        self.minsize(860, 560)

        self.settings = Settings.carregar()
        self.tema = aplicar_tema(self, obter_tema(self.settings.tema))
        self.automador = Automador(self.settings)
        self.biblioteca = Biblioteca(self.automador.pasta_saida)
        self.ultimo_modulo = ""

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

    def salvar_print(self, imagem: Image.Image) -> None:
        """Pergunta modulo, nome e acao no centro da tela e guarda o print."""
        dados = pedir_dados_print(self, self.biblioteca.modulos(), self.ultimo_modulo)
        if dados is None:
            return
        modulo, nome, acao = dados
        if self.biblioteca.existe(modulo, nome) and not messagebox.askyesno(
            "Substituir", f"'{modulo}/{nome}.png' ja existe. Substituir?", parent=self
        ):
            return
        self.biblioteca.salvar(imagem, modulo, nome, acao)
        self.ultimo_modulo = modulo
        self.gerar_codigo()
        self.captura.atualizar_lista(selecionar=f"{modulo}/{nome}.png")
        aviso_temporario(self, f"Print salvo: {modulo}/{nome}.png")

    def exportar_projeto(self) -> None:
        """Copia src/ e o guia de integracao para a pasta de um projeto."""
        destino = filedialog.askdirectory(parent=self, title="Pasta do projeto onde o codigo vai ser colado")
        if not destino:
            return
        self.gerar_codigo()
        try:
            resultado = self.biblioteca.exportar(Path(destino))
        except OSError as erro:
            messagebox.showerror("Exportar projeto", str(erro), parent=self)
            return
        self.registrar(f"Exportado para {destino}: {len(resultado.copiados)} arquivo(s) novos.")
        if resultado.ignorados:
            messagebox.showinfo(
                "Exportar projeto",
                "Ja existiam no projeto e nao foram substituidos:\n\n"
                + "\n".join(resultado.ignorados)
                + "\n\nCole os metodos deles a mao, usando o botao Codigo do modulo.",
                parent=self,
            )
        else:
            aviso_temporario(self, f"Projeto exportado: {len(resultado.copiados)} arquivo(s)")

    def salvar_desvio_print(self, nome: str, dx: int | None, dy: int | None) -> None:
        """Desvio proprio de um print. Com dx None, o print volta a usar o desvio padrao."""
        self.biblioteca.definir_desvio(nome, dx, dy)
        self.gerar_codigo()
        if dx is None:
            self.registrar(f"Desvio de {nome} removido: usa o desvio padrao.")
        else:
            self.registrar(f"Desvio de {nome} salvo: dx={dx}, dy={dy}")

    def gerar_codigo(self) -> None:
        try:
            self.biblioteca.gerar_codigo()
        except OSError as erro:
            self.registrar(f"Falha ao gerar o codigo: {erro}")

    def medir_na_tela(self, ao_concluir: Callable[[int, int], None]) -> None:
        """Esconde o app e mede um desvio com dois cliques na tela congelada."""
        self.withdraw()
        self.after(300, lambda: medir_desvio(self, lambda desvio: self._fim_medicao(desvio, ao_concluir)))

    def medir_ancorado(self, ao_concluir: Callable[[Image.Image | None, tuple[int, int] | None], None]) -> None:
        """Esconde o app e mede o desvio a partir do quadrado escolhido na tela."""
        self.withdraw()
        self.after(300, lambda: abrir_medicao_ancorada(self, lambda recorte, desvio: self._fim_medicao_ancorada(recorte, desvio, ao_concluir)))

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

    def _fim_medicao_ancorada(self, recorte, desvio, ao_concluir) -> None:
        self.deiconify()
        ao_concluir(recorte, desvio)


def main() -> None:
    ativar_dpi()
    configurar_registro()
    logger.info("Visual Automator iniciado")
    App().mainloop()
