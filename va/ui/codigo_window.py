"""Janela 'Codigo do modulo': mostra o que colar no projeto, com botoes de copiar."""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from va.ui.dialogs import aviso_temporario

if TYPE_CHECKING:
    from va.ui.app import App


class CodigoWindow(tk.Toplevel):
    def __init__(self, app: "App"):
        super().__init__(app)
        self.title("Codigo do modulo")
        self.geometry("980x680")
        self.transient(app)
        self._app = app

        modulos = app.biblioteca.modulos()
        self._var_modulo = tk.StringVar(value=modulos[0] if modulos else "")

        topo = ttk.Frame(self, padding=10)
        topo.pack(fill="x")
        ttk.Label(topo, text="Modulo").pack(side="left")
        combo = ttk.Combobox(topo, textvariable=self._var_modulo, values=modulos, state="readonly", width=30)
        combo.pack(side="left", padx=8)
        combo.bind("<<ComboboxSelected>>", lambda _evento: self._mostrar())
        ttk.Label(
            topo,
            text="Copie cada bloco e cole no lugar indicado. Depois de colar, rode o projeto.",
            foreground="gray",
        ).pack(side="left", padx=12)

        self._texto_trecho = self._bloco(
            "1) Cole este trecho dentro de src/template_constants.py (ou substitua o arquivo gerado)"
        )
        self._texto_arquivo = self._bloco(
            "2) Arquivo src/services/<modulo>.py: crie se nao existir; substitua se ja existir"
        )
        self._mostrar()

    def _bloco(self, titulo: str) -> tk.Text:
        quadro = ttk.LabelFrame(self, text=titulo, padding=8)
        quadro.pack(fill="both", expand=True, padx=10, pady=6)
        texto = tk.Text(quadro, height=12, wrap="none", font=("Consolas", 10))
        texto.pack(fill="both", expand=True)
        ttk.Button(quadro, text="Copiar", command=lambda: self._copiar(texto)).pack(anchor="e", pady=(6, 0))
        return texto

    def _mostrar(self) -> None:
        modulo = self._var_modulo.get()
        if not modulo:
            return
        trecho, arquivo = self._app.biblioteca.codigo_do_modulo(modulo)
        _preencher(self._texto_trecho, trecho)
        _preencher(self._texto_arquivo, arquivo)

    def _copiar(self, texto: tk.Text) -> None:
        self.clipboard_clear()
        self.clipboard_append(texto.get("1.0", "end-1c"))
        aviso_temporario(self, "Copiado", ms=900)


def _preencher(texto: tk.Text, conteudo: str) -> None:
    texto.configure(state="normal")
    texto.delete("1.0", tk.END)
    texto.insert("1.0", conteudo)
    texto.configure(state="disabled")
