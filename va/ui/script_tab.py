"""Aba Roteiro: monta a sequencia de passos, salva/abre em JSON e executa."""

import json
import queue
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING

from va.automation.actions import ACOES_ROTEIRO
from va.automation.runner import Passo, Runner
from va.paths import BASE_DIR

if TYPE_CHECKING:
    from va.ui.app import App


class RoteiroTab(ttk.Frame):
    def __init__(self, master: tk.Misc, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self.passos: list[Passo] = []
        self._fila: queue.Queue[str] = queue.Queue()
        self._runner = Runner(self._executar_passo)
        self._montar()
        self.after(100, self._drenar_log)

    def _montar(self) -> None:
        formulario = ttk.LabelFrame(self, text="Novo passo", padding=8)
        formulario.pack(fill="x")

        self.var_acao = tk.StringVar(value=ACOES_ROTEIRO[0])
        self.var_alvo = tk.StringVar()
        self.var_valor = tk.StringVar()

        ttk.Label(formulario, text="Acao").grid(row=0, column=0, sticky="w")
        ttk.Combobox(formulario, textvariable=self.var_acao, values=ACOES_ROTEIRO, state="readonly", width=20).grid(row=1, column=0, padx=(0, 8), sticky="w")
        ttk.Label(formulario, text="Alvo (imagem, texto ou tecla)").grid(row=0, column=1, sticky="w")
        ttk.Entry(formulario, textvariable=self.var_alvo, width=34).grid(row=1, column=1, padx=(0, 8), sticky="we")
        ttk.Label(formulario, text="Valor (texto a digitar ou segundos)").grid(row=0, column=2, sticky="w")
        ttk.Entry(formulario, textvariable=self.var_valor, width=28).grid(row=1, column=2, padx=(0, 8), sticky="we")
        ttk.Button(formulario, text="Adicionar", command=self._adicionar_do_formulario).grid(row=1, column=3)
        formulario.columnconfigure(1, weight=1)

        meio = ttk.Frame(self)
        meio.pack(fill="both", expand=True, pady=8)

        self.tabela = ttk.Treeview(meio, columns=("acao", "alvo", "valor"), show="headings", height=8)
        for coluna, titulo, largura in (("acao", "Acao", 160), ("alvo", "Alvo", 300), ("valor", "Valor", 200)):
            self.tabela.heading(coluna, text=titulo)
            self.tabela.column(coluna, width=largura, anchor="w")
        self.tabela.pack(side="left", fill="both", expand=True)

        laterais = ttk.Frame(meio)
        laterais.pack(side="left", fill="y", padx=(8, 0))
        for texto, comando in (
            ("Remover", self.remover_passo),
            ("Subir", lambda: self.mover_passo(-1)),
            ("Descer", lambda: self.mover_passo(1)),
            ("Limpar roteiro", self.limpar_roteiro),
            ("Abrir roteiro...", self.abrir_roteiro),
            ("Salvar roteiro...", self.salvar_roteiro),
        ):
            ttk.Button(laterais, text=texto, command=comando, width=18).pack(fill="x", pady=2)

        controles = ttk.Frame(self)
        controles.pack(fill="x")
        tk.Button(
            controles, text="Executar", command=self.executar, bg="#16a34a", fg="white",
            font=("Segoe UI", 12, "bold"), relief="flat", width=14,
        ).pack(side="left")
        tk.Button(
            controles, text="Parar", command=self._runner.parar, bg="#dc2626", fg="white",
            font=("Segoe UI", 12, "bold"), relief="flat", width=10,
        ).pack(side="left", padx=8)
        ttk.Label(controles, text="Mouse no canto superior esquerdo interrompe tudo.", foreground="gray").pack(side="left", padx=8)

        self.texto_log = tk.Text(self, height=8, state="disabled", wrap="word")
        self.texto_log.pack(fill="both", expand=False, pady=(8, 0))

    def adicionar(self, passo: Passo) -> None:
        self.passos.append(passo)
        self._recarregar_tabela()

    def executar(self) -> None:
        if self._runner.ocupado:
            return
        if not self.passos:
            messagebox.showinfo("Roteiro vazio", "Adicione passos antes de executar.", parent=self.app)
            return
        self._runner.iniciar(list(self.passos), self._fila.put)

    def log(self, mensagem: str) -> None:
        self.texto_log.configure(state="normal")
        self.texto_log.insert(tk.END, mensagem + "\n")
        self.texto_log.see(tk.END)
        self.texto_log.configure(state="disabled")

    def _executar_passo(self, passo: Passo) -> None:
        self.app.automador.executar(passo.acao, passo.alvo, passo.valor)

    def _drenar_log(self) -> None:
        while True:
            try:
                self.log(self._fila.get_nowait())
            except queue.Empty:
                break
        self.after(100, self._drenar_log)

    def _adicionar_do_formulario(self) -> None:
        acao = self.var_acao.get()
        alvo = self.var_alvo.get().strip()
        valor = self.var_valor.get().strip()
        if not alvo and acao != "digitar":
            messagebox.showwarning("Campo vazio", "Informe o alvo do passo.", parent=self.app)
            return
        if not alvo and not valor:
            messagebox.showwarning("Campo vazio", "Informe o texto a digitar.", parent=self.app)
            return
        self.adicionar(Passo(acao, alvo, valor))
        self.var_alvo.set("")
        self.var_valor.set("")

    def _recarregar_tabela(self) -> None:
        self.tabela.delete(*self.tabela.get_children())
        for indice, passo in enumerate(self.passos):
            self.tabela.insert("", tk.END, iid=str(indice), values=(passo.acao, passo.alvo, passo.valor))

    def _indice_selecionado(self) -> int | None:
        selecao = self.tabela.selection()
        return int(selecao[0]) if selecao else None

    def remover_passo(self) -> None:
        indice = self._indice_selecionado()
        if indice is not None:
            del self.passos[indice]
            self._recarregar_tabela()

    def mover_passo(self, direcao: int) -> None:
        indice = self._indice_selecionado()
        if indice is None:
            return
        destino = indice + direcao
        if 0 <= destino < len(self.passos):
            self.passos[indice], self.passos[destino] = self.passos[destino], self.passos[indice]
            self._recarregar_tabela()
            self.tabela.selection_set(str(destino))

    def limpar_roteiro(self) -> None:
        if self.passos and messagebox.askyesno("Limpar", "Apagar todos os passos do roteiro?", parent=self.app):
            self.passos.clear()
            self._recarregar_tabela()

    def salvar_roteiro(self) -> None:
        caminho = filedialog.asksaveasfilename(
            parent=self.app, initialdir=BASE_DIR, defaultextension=".json",
            filetypes=[("Roteiro JSON", "*.json")],
        )
        if caminho:
            dados = {"passos": [passo.para_dict() for passo in self.passos]}
            with open(caminho, "w", encoding="utf-8") as arquivo:
                json.dump(dados, arquivo, indent=2, ensure_ascii=False)
            self.log(f"Roteiro salvo: {caminho}")

    def abrir_roteiro(self) -> None:
        caminho = filedialog.askopenfilename(
            parent=self.app, initialdir=BASE_DIR, filetypes=[("Roteiro JSON", "*.json")],
        )
        if caminho:
            with open(caminho, encoding="utf-8") as arquivo:
                self.passos = [Passo.de_dict(dados) for dados in json.load(arquivo)["passos"]]
            self._recarregar_tabela()
            self.log(f"Roteiro carregado: {caminho}")
