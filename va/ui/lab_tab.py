"""Aba Laboratorio: ajusta o desvio padrao do clique olhando o print com uma cruz no centro."""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from PIL import Image, ImageTk

from va.geometria import desvio_do_clique, escala_para, ponto_no_canvas

if TYPE_CHECKING:
    from va.ui.app import App

TAMANHO_CANVAS = (760, 520)
COR_FUNDO = "#1f2937"
COR_CRUZ = "#ef4444"
COR_DESVIO = "#facc15"


class AbaLaboratorio(ttk.Frame):
    def __init__(self, master: tk.Misc, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._imagem: Image.Image | None = None
        self._foto: ImageTk.PhotoImage | None = None
        self._escala = 1.0
        self._var_imagem = tk.StringVar()
        self._var_dx = tk.StringVar(value="0")
        self._var_dy = tk.StringVar(value="0")
        self._montar()
        self._var_dx.trace_add("write", lambda *_: self._atualizar_marcador())
        self._var_dy.trace_add("write", lambda *_: self._atualizar_marcador())
        self.mostrar_atual()

    def _montar(self) -> None:
        topo = ttk.Frame(self)
        topo.pack(fill="x")
        ttk.Label(topo, text="Print").pack(side="left")
        self.combo = ttk.Combobox(topo, textvariable=self._var_imagem, state="readonly", width=40)
        self.combo.pack(side="left", padx=8)
        self.combo.bind("<<ComboboxSelected>>", lambda _evento: self._carregar())

        corpo = ttk.Frame(self)
        corpo.pack(fill="both", expand=True, pady=(8, 0))

        largura, altura = TAMANHO_CANVAS
        self.canvas = tk.Canvas(corpo, width=largura, height=altura, bg=COR_FUNDO, highlightthickness=0, cursor="crosshair")
        self.canvas.pack(side="left")
        self.canvas.bind("<Button-1>", self._clicar)

        painel = ttk.LabelFrame(corpo, text="Desvio padrao do clique", padding=10)
        painel.pack(side="left", fill="y", padx=(12, 0))
        ttk.Label(
            painel,
            text="Clique na area para escolher o desvio.\nClicar fora do print tambem vale.",
            foreground="gray",
        ).pack(anchor="w")
        grade = ttk.Frame(painel)
        grade.pack(anchor="w", pady=10)
        ttk.Label(grade, text="dx (horizontal)").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Spinbox(grade, from_=-2000, to=2000, textvariable=self._var_dx, width=8).grid(row=0, column=1, padx=8)
        ttk.Label(grade, text="dy (vertical)").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Spinbox(grade, from_=-2000, to=2000, textvariable=self._var_dy, width=8).grid(row=1, column=1, padx=8)
        self.label_atual = ttk.Label(painel, text="")
        self.label_atual.pack(anchor="w")
        self.label_escolhido = ttk.Label(painel, text="")
        self.label_escolhido.pack(anchor="w", pady=(4, 12))
        botoes = ttk.Frame(painel)
        botoes.pack(anchor="w")
        ttk.Button(botoes, text="Zerar", command=self.zerar).pack(side="left")
        ttk.Button(botoes, text="Medir na tela", command=self.medir).pack(side="left", padx=(8, 0))
        ttk.Button(botoes, text="Salvar como desvio padrao", command=self.salvar).pack(side="left", padx=(8, 0))

    def atualizar_imagens(self, nomes: list[str], selecionar: str | None = None) -> None:
        self.combo["values"] = nomes
        if selecionar in nomes:
            self._var_imagem.set(selecionar)
        elif self._var_imagem.get() not in nomes:
            self._var_imagem.set(nomes[0] if nomes else "")
        self._carregar()

    def mostrar_atual(self) -> None:
        settings = self.app.settings
        self.label_atual.configure(text=f"Desvio padrao atual: dx={settings.offset_x}, dy={settings.offset_y}")

    def preencher(self, dx: int, dy: int) -> None:
        self._var_dx.set(str(dx))
        self._var_dy.set(str(dy))

    def zerar(self) -> None:
        self.preencher(0, 0)

    def medir(self) -> None:
        """Abre a tela para medir o desvio com dois cliques; o resultado preenche dx e dy."""
        self.app.medir_na_tela(self.preencher)

    def salvar(self) -> None:
        desvio = self._lerdesvio()
        if desvio is None:
            messagebox.showwarning("Valor invalido", "Use numeros inteiros em dx e dy.", parent=self.app)
            return
        self.app.salvar_desvio_padrao(*desvio)
        self.mostrar_atual()

    def _carregar(self) -> None:
        self.canvas.delete("all")
        self._foto = None
        self._imagem = None
        nome = self._var_imagem.get()
        if nome:
            with Image.open(self.app.biblioteca.caminho(nome)) as arquivo:
                self._imagem = arquivo.convert("RGB")
        if self._imagem is not None:
            self._desenhar_imagem()
        self._desenhar_cruz()
        self._atualizar_marcador()

    def _desenhar_imagem(self) -> None:
        largura, altura = self._imagem.size
        cw, ch = TAMANHO_CANVAS
        self._escala = escala_para(largura, altura, cw, ch)
        nova_largura = max(1, round(largura * self._escala))
        nova_altura = max(1, round(altura * self._escala))
        self._foto = ImageTk.PhotoImage(self._imagem.resize((nova_largura, nova_altura), Image.Resampling.LANCZOS))
        self.canvas.create_image(cw / 2, ch / 2, image=self._foto)
        self.canvas.create_rectangle(
            cw / 2 - nova_largura / 2,
            ch / 2 - nova_altura / 2,
            cw / 2 + nova_largura / 2,
            ch / 2 + nova_altura / 2,
            outline="#9ca3af",
            dash=(4, 4),
        )

    def _desenhar_cruz(self) -> None:
        cw, ch = TAMANHO_CANVAS
        self.canvas.create_line(cw / 2, 0, cw / 2, ch, fill=COR_CRUZ, width=1)
        self.canvas.create_line(0, ch / 2, cw, ch / 2, fill=COR_CRUZ, width=1)
        self.canvas.create_oval(cw / 2 - 4, ch / 2 - 4, cw / 2 + 4, ch / 2 + 4, outline=COR_CRUZ, width=2)

    def _clicar(self, evento) -> None:
        cw, ch = TAMANHO_CANVAS
        dx, dy = desvio_do_clique(evento.x, evento.y, cw, ch, self._escala)
        self.preencher(dx, dy)

    def _atualizar_marcador(self) -> None:
        self.canvas.delete("marcador")
        desvio = self._lerdesvio()
        if desvio is None:
            self.label_escolhido.configure(text="Valor invalido: use numeros inteiros")
            return
        dx, dy = desvio
        cw, ch = TAMANHO_CANVAS
        x, y = ponto_no_canvas(dx, dy, cw, ch, self._escala)
        self.canvas.create_line(cw / 2, ch / 2, x, y, fill=COR_DESVIO, dash=(4, 3), tags="marcador")
        self.canvas.create_oval(x - 6, y - 6, x + 6, y + 6, fill=COR_DESVIO, outline="", tags="marcador")
        self.canvas.create_text(x + 10, y - 10, anchor="sw", fill=COR_DESVIO, text=f"{dx}, {dy}", tags="marcador")
        self.label_escolhido.configure(text=f"Escolhido: dx={dx}, dy={dy}")

    def _lerdesvio(self) -> tuple[int, int] | None:
        try:
            return int(self._var_dx.get()), int(self._var_dy.get())
        except ValueError:
            return None
