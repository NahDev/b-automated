"""Aba Laboratorio: ajusta o desvio padrao do clique olhando o print com uma cruz no centro.

Tambem testa o print na tela e mede o desvio de forma ancorada: o quadrado do print e o ponto do clique,
ambos escolhidos na tela congelada.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from PIL import Image, ImageTk

from va.geometria import desvio_do_clique, escala_para, ponto_no_canvas
from va.ui.locate_window import JanelaTesteLocalizacao

if TYPE_CHECKING:
    from va.ui.app import App

TAMANHO_CANVAS = (760, 520)
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
        self.combo.bind("<<ComboboxSelected>>", lambda _evento: self._ao_escolher())

        corpo = ttk.Frame(self)
        corpo.pack(fill="both", expand=True, pady=(8, 0))

        largura, altura = TAMANHO_CANVAS
        self.canvas = tk.Canvas(corpo, width=largura, height=altura, bg=self.app.tema.visual, highlightthickness=0, cursor="crosshair")
        self.canvas.pack(side="left")
        self.canvas.bind("<Button-1>", self._clicar)

        painel = ttk.LabelFrame(corpo, text="Desvio padrao do clique", padding=10)
        painel.pack(side="left", fill="y", padx=(12, 0))
        ttk.Label(
            painel,
            text="Clique na area para escolher o desvio.\nClicar fora do print tambem vale.",
            style="Dica.TLabel",
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

        acoes = ttk.LabelFrame(painel, text="Testar e medir", padding=8)
        acoes.pack(fill="x")
        ttk.Button(acoes, text="Testar na tela", command=self.testar).pack(fill="x", pady=2)
        ttk.Button(acoes, text="Medir ancorado (quadrado + clique)", command=self.medir_ancorado).pack(fill="x", pady=2)
        ttk.Button(acoes, text="Medir na tela (2 cliques)", command=self.medir).pack(fill="x", pady=2)

        por_print = ttk.LabelFrame(painel, text="Desvio deste print", padding=8)
        por_print.pack(fill="x", pady=(0, 8))
        self.label_print = ttk.Label(por_print, text="")
        self.label_print.pack(anchor="w")
        ttk.Button(por_print, text="Salvar desvio deste print", command=self.salvar_desvio_print).pack(fill="x", pady=2)
        ttk.Button(por_print, text="Remover (usar o desvio padrao)", command=self.remover_desvio_print).pack(fill="x", pady=2)

        botoes = ttk.Frame(painel)
        botoes.pack(anchor="w", pady=(12, 0))
        ttk.Button(botoes, text="Zerar", command=self.zerar).pack(side="left")
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

    def testar(self) -> None:
        """Procura o print escolhido na tela e mostra as ocorrencias para escolher uma."""
        nome = self._var_imagem.get()
        if not nome:
            messagebox.showinfo("Sem print", "Escolha um print na lista acima.", parent=self.app)
            return
        JanelaTesteLocalizacao(self.app, nome)

    def medir(self) -> None:
        """Mede o desvio com dois cliques: centro da referencia e ponto do clique."""
        self.app.medir_na_tela(self.preencher)

    def medir_ancorado(self) -> None:
        """Mede o desvio a partir do quadrado escolhido na tela; pode salvar o quadrado como print."""
        self.app.medir_ancorado(self._fim_medicao_ancorada)

    def salvar(self) -> None:
        desvio = self._lerdesvio()
        if desvio is None:
            messagebox.showwarning("Valor invalido", "Use numeros inteiros em dx e dy.", parent=self.app)
            return
        self.app.salvar_desvio_padrao(*desvio)
        self.mostrar_atual()

    def _fim_medicao_ancorada(self, recorte: Image.Image | None, desvio: tuple[int, int] | None) -> None:
        if desvio is not None:
            self.preencher(*desvio)
        if recorte is not None and messagebox.askyesno(
            "Salvar print", "Salvar o quadrado selecionado como print?", parent=self.app
        ):
            self.app.salvar_print(recorte)

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
        self.mostrar_desvio_print()

    def _ao_escolher(self) -> None:
        """Ao escolher um print, mostra o desvio dele nos campos (se tiver um proprio)."""
        self._carregar()
        desvio = self.app.biblioteca.desvio_do_print(self._var_imagem.get()) if self._var_imagem.get() else None
        if desvio is not None:
            self.preencher(*desvio)

    def mostrar_desvio_print(self) -> None:
        nome = self._var_imagem.get()
        desvio = self.app.biblioteca.desvio_do_print(nome) if nome else None
        if desvio is None:
            self.label_print.configure(text="Este print usa o desvio padrao.")
        else:
            self.label_print.configure(text=f"Desvio deste print: dx={desvio[0]}, dy={desvio[1]}")

    def salvar_desvio_print(self) -> None:
        nome = self._var_imagem.get()
        desvio = self._lerdesvio()
        if not nome:
            messagebox.showinfo("Sem print", "Escolha um print na lista acima.", parent=self.app)
            return
        if desvio is None:
            messagebox.showwarning("Valor invalido", "Use numeros inteiros em dx e dy.", parent=self.app)
            return
        self.app.salvar_desvio_print(nome, *desvio)
        self.mostrar_desvio_print()

    def remover_desvio_print(self) -> None:
        nome = self._var_imagem.get()
        if nome:
            self.app.salvar_desvio_print(nome, None, None)
            self.mostrar_desvio_print()

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
