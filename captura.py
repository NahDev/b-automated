"""Captura de tela com selecao por arrastar, para tirar os prints dos alvos."""

import tkinter as tk
from typing import Callable

import pyautogui
from PIL import Image, ImageTk


def selecionar_regiao(master: tk.Misc, ao_concluir: Callable[[Image.Image | None], None]) -> None:
    """Mostra a tela congelada em tela cheia. O usuario arrasta um retangulo e
    recebe o recorte; Esc ou um arrasto muito pequeno cancela (recebe None)."""
    tela = pyautogui.screenshot()
    largura, altura = tela.size

    janela = tk.Toplevel(master)
    janela.overrideredirect(True)
    janela.geometry(f"{largura}x{altura}+0+0")
    janela.attributes("-topmost", True)

    foto = ImageTk.PhotoImage(tela)
    canvas = tk.Canvas(janela, width=largura, height=altura, highlightthickness=0, cursor="crosshair")
    canvas.pack()
    canvas.create_image(0, 0, anchor="nw", image=foto)
    canvas.create_text(
        20, 20, anchor="nw", fill="yellow", font=("Segoe UI", 14, "bold"),
        text="Arraste para selecionar o alvo. Esc cancela.",
    )
    janela.foto = foto  # mantem a referencia viva enquanto a janela existir

    inicio = {"x": 0, "y": 0, "retangulo": None}

    def ao_pressionar(evento):
        inicio["x"], inicio["y"] = evento.x, evento.y
        inicio["retangulo"] = canvas.create_rectangle(
            evento.x, evento.y, evento.x, evento.y, outline="red", width=2
        )

    def ao_arrastar(evento):
        if inicio["retangulo"] is not None:
            canvas.coords(inicio["retangulo"], inicio["x"], inicio["y"], evento.x, evento.y)

    def ao_soltar(evento):
        x0, x1 = sorted((inicio["x"], evento.x))
        y0, y1 = sorted((inicio["y"], evento.y))
        janela.destroy()
        if x1 - x0 < 3 or y1 - y0 < 3:
            ao_concluir(None)
            return
        ao_concluir(tela.crop((x0, y0, x1, y1)))

    def cancelar(_evento=None):
        janela.destroy()
        ao_concluir(None)

    canvas.bind("<ButtonPress-1>", ao_pressionar)
    canvas.bind("<B1-Motion>", ao_arrastar)
    canvas.bind("<ButtonRelease-1>", ao_soltar)
    janela.bind("<Escape>", cancelar)
    janela.focus_force()
    canvas.focus_set()


def desvio_entre(ponto_centro: tuple[int, int], ponto_alvo: tuple[int, int]) -> tuple[int, int]:
    """Desvio (dx, dy) do ponto alvo em relacao ao centro da referencia."""
    return ponto_alvo[0] - ponto_centro[0], ponto_alvo[1] - ponto_centro[1]


def medir_desvio(master: tk.Misc, ao_concluir: Callable[[tuple[int, int] | None], None]) -> None:
    """Mostra a tela congelada para medir o desvio. 1o clique: centro da referencia.
    2o clique: ponto desejado. Enter aceita e devolve (dx, dy); Esc cancela (devolve None).
    Um 3o clique recomeca a medicao."""
    tela = pyautogui.screenshot()
    largura, altura = tela.size

    janela = tk.Toplevel(master)
    janela.overrideredirect(True)
    janela.geometry(f"{largura}x{altura}+0+0")
    janela.attributes("-topmost", True)

    foto = ImageTk.PhotoImage(tela)
    canvas = tk.Canvas(janela, width=largura, height=altura, highlightthickness=0, cursor="crosshair")
    canvas.pack()
    canvas.create_image(0, 0, anchor="nw", image=foto)
    canvas.create_text(
        20, 20, anchor="nw", fill="yellow", font=("Segoe UI", 14, "bold"),
        text="1o clique: centro da referencia. 2o clique: ponto desejado. Enter aceita, Esc cancela.",
    )
    janela.foto = foto  # mantem a referencia viva enquanto a janela existir

    pontos: list[tuple[int, int]] = []

    def desenhar_cruz(x: int, y: int, cor: str):
        canvas.create_line(x - 12, y, x + 12, y, fill=cor, width=2, tags="medicao")
        canvas.create_line(x, y - 12, x, y + 12, fill=cor, width=2, tags="medicao")

    def ao_clicar(evento):
        if len(pontos) == 2:
            pontos.clear()
            canvas.delete("medicao")
        pontos.append((evento.x, evento.y))
        desenhar_cruz(evento.x, evento.y, "red")
        if len(pontos) == 2:
            (x1, y1), (x2, y2) = pontos
            dx, dy = desvio_entre(pontos[0], pontos[1])
            canvas.create_line(x1, y1, x2, y2, fill="yellow", width=2, dash=(6, 4), tags="medicao")
            texto = f"dx={dx}  dy={dy}   (Enter aceita)"
            canvas.create_rectangle(
                x2 + 12, y2 + 12, x2 + 24 + len(texto) * 10, y2 + 42,
                fill="black", outline="yellow", tags="medicao",
            )
            canvas.create_text(
                x2 + 18, y2 + 18, anchor="nw", fill="yellow", font=("Segoe UI", 14, "bold"),
                text=texto, tags="medicao",
            )

    def aceitar(_evento=None):
        if len(pontos) != 2:
            return
        janela.destroy()
        ao_concluir(desvio_entre(pontos[0], pontos[1]))

    def cancelar(_evento=None):
        janela.destroy()
        ao_concluir(None)

    canvas.bind("<Button-1>", ao_clicar)
    janela.bind("<Return>", aceitar)
    janela.bind("<Escape>", cancelar)
    canvas.bind("<Return>", aceitar)
    canvas.bind("<Escape>", cancelar)
    janela.focus_force()
    canvas.focus_set()
