"""Aba Capturar: tira prints da tela, mostra os prints guardados e exporta o codigo para o projeto."""

import os
import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from PIL import Image, ImageTk

from va.automation.runner import Passo
from va.ui.codigo_window import CodigoWindow
from va.ui.overlay import selecionar_regiao

if TYPE_CHECKING:
    from va.ui.app import App


class CapturaTab(ttk.Frame):
    def __init__(self, master: tk.Misc, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._nomes: list[str] = []
        self._foto_preview: ImageTk.PhotoImage | None = None
        self._montar()

    def _montar(self) -> None:
        topo = ttk.Frame(self)
        topo.pack(fill="x")
        tk.Button(
            topo, text="Capturar regiao (F9)", command=self.capturar,
            font=("Segoe UI", 16, "bold"), bg="#2563eb", fg="white",
            activebackground="#1d4ed8", activeforeground="white", relief="flat", height=2,
        ).pack(fill="x")
        ttk.Label(
            topo,
            text="Clique no botao (ou F9), arraste sobre o alvo e solte. Depois informe o modulo (pagina), o nome do print e a acao padrao.",
            foreground="gray",
        ).pack(anchor="w", pady=(6, 10))

        corpo = ttk.Frame(self)
        corpo.pack(fill="both", expand=True)

        esquerda = ttk.Frame(corpo)
        esquerda.pack(side="left", fill="y")
        ttk.Label(esquerda, text="Imagens capturadas").pack(anchor="w")
        self.lista = tk.Listbox(esquerda, width=34, exportselection=False)
        self.lista.pack(fill="y", expand=True)
        self.lista.bind("<<ListboxSelect>>", lambda _evento: self._mostrar_selecionada())

        botoes = ttk.Frame(esquerda)
        botoes.pack(fill="x", pady=6)
        ttk.Button(botoes, text="Adicionar ao roteiro", command=self.adicionar_selecionada_ao_roteiro).pack(fill="x", pady=2)
        ttk.Button(botoes, text="Excluir", command=self.excluir_selecionada).pack(fill="x", pady=2)
        ttk.Button(botoes, text="Atualizar lista", command=self.atualizar_lista).pack(fill="x", pady=2)
        ttk.Separator(botoes).pack(fill="x", pady=6)
        ttk.Button(botoes, text="Codigo do modulo...", command=lambda: CodigoWindow(self.app)).pack(fill="x", pady=2)
        ttk.Button(botoes, text="Exportar projeto...", command=self.app.exportar_projeto).pack(fill="x", pady=2)
        ttk.Button(botoes, text="Abrir pasta de saida", command=self.abrir_pasta_saida).pack(fill="x", pady=2)

        direita = ttk.LabelFrame(corpo, text="Visualizacao", padding=10)
        direita.pack(side="left", fill="both", expand=True, padx=(12, 0))
        self.label_preview = ttk.Label(direita, text="Selecione uma imagem")
        self.label_preview.pack(expand=True)

    def capturar(self) -> None:
        self.app.withdraw()
        self.after(300, lambda: selecionar_regiao(self.app, self._apos_captura))

    def atualizar_lista(self, selecionar: str | None = None) -> None:
        self._nomes = self.app.biblioteca.nomes()
        self.lista.delete(0, tk.END)
        for nome in self._nomes:
            self.lista.insert(tk.END, nome)
        if selecionar in self._nomes:
            self.lista.selection_set(self._nomes.index(selecionar))
            self._mostrar_selecionada()
        self.app.laboratorio.atualizar_imagens(self._nomes, selecionar)

    def adicionar_selecionada_ao_roteiro(self) -> None:
        nome = self._nome_selecionado()
        if nome is not None:
            self.app.roteiro.adicionar(Passo("clicar_imagem", nome))

    def excluir_selecionada(self) -> None:
        nome = self._nome_selecionado()
        if nome is None:
            return
        if not messagebox.askyesno("Excluir", f"Excluir a imagem '{nome}'?", parent=self.app):
            return
        self.app.biblioteca.excluir(nome)
        self.app.gerar_codigo()
        self.atualizar_lista()
        self.label_preview.configure(image="", text="Selecione uma imagem")

    def abrir_pasta_saida(self) -> None:
        pasta = self.app.biblioteca.pasta_saida
        pasta.mkdir(parents=True, exist_ok=True)
        os.startfile(pasta)

    def _apos_captura(self, imagem: Image.Image | None) -> None:
        self.app.deiconify()
        if imagem is not None:
            self.app.salvar_print(imagem)

    def _nome_selecionado(self) -> str | None:
        selecao = self.lista.curselection()
        return self._nomes[selecao[0]] if selecao else None

    def _mostrar_selecionada(self) -> None:
        nome = self._nome_selecionado()
        if nome is None:
            return
        with Image.open(self.app.biblioteca.caminho(nome)) as imagem:
            miniatura = imagem.copy()
        miniatura.thumbnail((560, 420))
        self._foto_preview = ImageTk.PhotoImage(miniatura)
        self.label_preview.configure(image=self._foto_preview, text="")
