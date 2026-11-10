"""Janela de teste de localizacao: mostra onde o print foi achado, lista as ocorrencias com indice
e confianca, e permite clicar em uma delas ou ajustar a confianca."""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

import pyautogui
from PIL import Image, ImageTk

from va.automation.vision import Ocorrencia, buscar_ocorrencias

if TYPE_CHECKING:
    from va.ui.app import App

TAMANHO_CANVAS = (900, 620)
COR_OCORRENCIA = "#ef4444"
COR_SELECIONADA = "#facc15"
COR_MELHOR = "#fb923c"


class JanelaTesteLocalizacao(tk.Toplevel):
    def __init__(self, app: "App", nome: str):
        super().__init__(app)
        self.title(f"Testar localizacao: {nome}")
        self.geometry("1260x720")
        self.transient(app)
        self._app = app
        self._nome = nome
        self._tela: Image.Image | None = None
        self._foto: ImageTk.PhotoImage | None = None
        self._escala = 1.0
        self._ocorrencias: list[Ocorrencia] = []
        self._melhor: Ocorrencia | None = None
        self._var_confianca = tk.StringVar(value=f"{app.settings.confianca:.2f}")
        self._var_status = tk.StringVar(value="Capturando a tela...")
        self._montar()
        self.after(50, self.testar)

    def destroy(self) -> None:
        self._app.deiconify()
        super().destroy()

    def testar(self) -> None:
        """Esconde a janela e o app, tira um print da tela e procura o alvo."""
        self.withdraw()
        self._app.withdraw()
        self.after(400, self._tirar_print)

    def clicar_selecionada(self) -> None:
        selecao = self.tabela.selection()
        if not selecao:
            messagebox.showinfo("Escolha uma ocorrencia", "Selecione um indice na tabela.", parent=self)
            return
        centro_x, centro_y = self._ocorrencias[int(selecao[0])].centro
        settings = self._app.settings
        ponto = (centro_x + settings.offset_x, centro_y + settings.offset_y)
        self.withdraw()
        self._app.withdraw()
        self.after(400, lambda: self._executar_clique(ponto))

    def _montar(self) -> None:
        corpo = ttk.Frame(self, padding=10)
        corpo.pack(fill="both", expand=True)

        largura, altura = TAMANHO_CANVAS
        self.canvas = tk.Canvas(corpo, width=largura, height=altura, bg="#111827", highlightthickness=0)
        self.canvas.pack(side="left")

        painel = ttk.Frame(corpo, padding=(12, 0, 0, 0))
        painel.pack(side="left", fill="both", expand=True)
        ttk.Label(painel, textvariable=self._var_status, wraplength=320, justify="left").pack(anchor="w")

        linha = ttk.Frame(painel)
        linha.pack(anchor="w", pady=8)
        ttk.Label(linha, text="Confianca (0 a 1)").pack(side="left")
        ttk.Spinbox(linha, from_=0.10, to=1.00, increment=0.01, textvariable=self._var_confianca, width=6).pack(side="left", padx=6)
        ttk.Button(linha, text="Testar de novo", command=self.testar).pack(side="left")

        self.tabela = ttk.Treeview(
            painel,
            columns=("indice", "x", "y", "largura", "altura", "confianca"),
            show="headings",
            height=14,
            selectmode="browse",
        )
        for coluna, titulo, largura_coluna in (
            ("indice", "Indice", 60),
            ("x", "X", 60),
            ("y", "Y", 60),
            ("largura", "Largura", 70),
            ("altura", "Altura", 70),
            ("confianca", "Confianca", 80),
        ):
            self.tabela.heading(coluna, text=titulo)
            self.tabela.column(coluna, width=largura_coluna, anchor="center")
        self.tabela.pack(fill="both", expand=True)
        self.tabela.bind("<<TreeviewSelect>>", lambda _evento: self._desenhar())
        self.tabela.bind("<Double-1>", lambda _evento: self.clicar_selecionada())

        botoes = ttk.Frame(painel)
        botoes.pack(anchor="w", pady=8)
        ttk.Button(botoes, text="Clicar na selecionada", command=self.clicar_selecionada).pack(side="left")
        ttk.Button(botoes, text="Usar esta confianca como padrao", command=self._salvar_confianca).pack(side="left", padx=6)

    def _tirar_print(self) -> None:
        self._tela = pyautogui.screenshot()
        self._app.deiconify()
        self.deiconify()
        self.lift()
        self._processar()

    def _processar(self) -> None:
        confianca = self._ler_confianca()
        if confianca is None:
            messagebox.showwarning("Valor invalido", "Use um numero entre 0 e 1 na confianca.", parent=self)
            return
        self._ocorrencias, self._melhor = buscar_ocorrencias(
            self._tela,
            self._app.automador.caminho_imagem(self._nome),
            confianca,
            self._app.settings.escala_cinza,
        )
        self._preencher_tabela()
        self._mostrar_status(confianca)
        self._desenhar()

    def _mostrar_status(self, confianca: float) -> None:
        if self._ocorrencias:
            self._var_status.set(
                f"{len(self._ocorrencias)} ocorrencia(s) com confianca >= {confianca:.2f}.\n"
                "Escolha o indice na tabela e clique em 'Clicar na selecionada' ou de duplo clique."
            )
        elif self._melhor is not None:
            score = self._melhor.confianca
            sugestao = max(0.10, round(score - 0.01, 2))
            self._var_status.set(
                f"Nao encontrada com confianca >= {confianca:.2f}.\n"
                f"Melhor semelhanca: {score:.2f} (laranja na tela).\n"
                f"Se for a imagem certa, tente confianca {sugestao:.2f}."
            )
        else:
            self._var_status.set("Nao encontrada: o print nao cabe na tela ou nao tem variacao para comparar.")

    def _preencher_tabela(self) -> None:
        self.tabela.delete(*self.tabela.get_children())
        for indice, ocorrencia in enumerate(self._ocorrencias):
            self.tabela.insert(
                "", tk.END, iid=str(indice),
                values=(indice + 1, ocorrencia.x, ocorrencia.y, ocorrencia.largura, ocorrencia.altura, f"{ocorrencia.confianca:.2f}"),
            )

    def _desenhar(self) -> None:
        self.canvas.delete("all")
        if self._tela is None:
            return
        cw, ch = TAMANHO_CANVAS
        tela_w, tela_h = self._tela.size
        self._escala = min(cw / tela_w, ch / tela_h, 1.0)
        nova = self._tela.resize(
            (max(1, round(tela_w * self._escala)), max(1, round(tela_h * self._escala))),
            Image.Resampling.LANCZOS,
        )
        self._foto = ImageTk.PhotoImage(nova)
        self.canvas.create_image(0, 0, anchor="nw", image=self._foto)

        selecao = self.tabela.selection()
        indice_selecionado = int(selecao[0]) if selecao else None
        for indice, ocorrencia in enumerate(self._ocorrencias):
            cor = COR_SELECIONADA if indice == indice_selecionado else COR_OCORRENCIA
            self._caixa(ocorrencia, cor, str(indice + 1))
        if not self._ocorrencias and self._melhor is not None:
            self._caixa(self._melhor, COR_MELHOR, f"{self._melhor.confianca:.2f}")

    def _caixa(self, ocorrencia: Ocorrencia, cor: str, rotulo: str) -> None:
        e = self._escala
        x, y = ocorrencia.x * e, ocorrencia.y * e
        self.canvas.create_rectangle(
            x, y, (ocorrencia.x + ocorrencia.largura) * e, (ocorrencia.y + ocorrencia.altura) * e, outline=cor, width=3
        )
        self.canvas.create_text(x + 4, y - 2, anchor="sw", fill=cor, font=("Segoe UI", 12, "bold"), text=rotulo)

    def _executar_clique(self, ponto: tuple[int, int]) -> None:
        pyautogui.moveTo(ponto[0], ponto[1], duration=self._app.settings.duracao_movimento)
        pyautogui.click(ponto[0], ponto[1])
        self._app.deiconify()
        self.deiconify()
        self.lift()

    def _salvar_confianca(self) -> None:
        confianca = self._ler_confianca()
        if confianca is None:
            messagebox.showwarning("Valor invalido", "Use um numero entre 0 e 1 na confianca.", parent=self)
            return
        self._app.salvar_confianca_padrao(confianca)

    def _ler_confianca(self) -> float | None:
        try:
            valor = float(self._var_confianca.get().replace(",", "."))
        except ValueError:
            return None
        return valor if 0 < valor <= 1 else None
