"""Temas visuais: cores e fontes da interface.

Um tema e so dados (cores e nomes de fonte, em ordem de preferencia). `aplicar` configura o ttk
com o tema escolhido e devolve o tema com a fonte que o computador realmente tem instalada.
As abas leem as cores pelo tema recebido, sem valores fixos no codigo.

O tema "btime" usa os tokens do design system (btime-tokens.json, modo claro). A fonte Branding
so aparece se estiver instalada no Windows; sem ela, usa Segoe UI.
"""

from dataclasses import dataclass, replace
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


@dataclass(frozen=True)
class Tema:
    nome: str
    tema_ttk: str  # tema base do ttk que aceita cores ("clam" aceita; "vista" nao)
    familias_corpo: tuple[str, ...]
    familias_destaque: tuple[str, ...]
    fundo: str
    superficie: str
    texto: str
    secundario: str
    borda: str
    primaria: str
    texto_primaria: str
    ativo: str  # cor de botoes e linhas selecionadas ao passar o mouse
    sucesso: str
    perigo: str
    visual: str  # fundo das telas que mostram imagens (laboratorio, teste na tela)
    familia_corpo: str = ""  # preenchidas por `aplicar`
    familia_destaque: str = ""

    def fonte(self, tamanho: int = 10, destaque: bool = False) -> tuple[str, int]:
        return (self.familia_destaque if destaque else self.familia_corpo, tamanho)


BTIME = Tema(
    nome="btime",
    tema_ttk="clam",
    familias_corpo=("Branding Semilight", "Branding", "Segoe UI"),
    familias_destaque=("Branding Semibold", "Branding", "Segoe UI"),
    fundo="#F7F6FB",  # background
    superficie="#FFFFFF",  # surface
    texto="#060315",  # text
    secundario="#62596F",  # muted
    borda="#E1DDEB",  # divider
    primaria="#571EE6",  # primary
    texto_primaria="#FFFFFF",  # onPrimary
    ativo="#D5C5FF",  # lavender
    sucesso="#16634B",  # status.success.text
    perigo="#B42343",  # status.error.text
    visual="#060315",  # night
)

NEUTRO = Tema(
    nome="neutro",
    tema_ttk="clam",
    familias_corpo=("Segoe UI",),
    familias_destaque=("Segoe UI Semibold", "Segoe UI"),
    fundo="#F0F0F0",
    superficie="#FFFFFF",
    texto="#111111",
    secundario="#6B7280",
    borda="#D1D5DB",
    primaria="#2563EB",
    texto_primaria="#FFFFFF",
    ativo="#E5E7EB",
    sucesso="#16A34A",
    perigo="#DC2626",
    visual="#111827",
)

TEMAS: dict[str, Tema] = {tema.nome: tema for tema in (BTIME, NEUTRO)}
TEMA_PADRAO = BTIME.nome


def obter(nome: str) -> Tema:
    """Devolve o tema pelo nome. Nome desconhecido (ex.: config antiga) cai no tema padrao."""
    return TEMAS.get(nome, TEMAS[TEMA_PADRAO])


def escolher_familia(candidatas: tuple[str, ...], disponiveis: set[str] | frozenset[str]) -> str:
    """Primeira familia da lista que esta instalada; se nenhuma estiver, a ultima (fallback)."""
    for familia in candidatas:
        if familia in disponiveis:
            return familia
    return candidatas[-1]


def aplicar(raiz: tk.Tk, tema: Tema) -> Tema:
    """Configura o ttk e o fundo da janela. Devolve o tema com as fontes resolvidas."""
    disponiveis = frozenset(tkfont.families(raiz))
    tema = replace(
        tema,
        familia_corpo=escolher_familia(tema.familias_corpo, disponiveis),
        familia_destaque=escolher_familia(tema.familias_destaque, disponiveis),
    )

    estilo = ttk.Style(raiz)
    estilo.theme_use(tema.tema_ttk)
    estilo.configure(".", background=tema.fundo, foreground=tema.texto, font=(tema.familia_corpo, 10),
                     bordercolor=tema.borda, lightcolor=tema.superficie, darkcolor=tema.borda)
    estilo.configure("TFrame", background=tema.fundo)
    estilo.configure("TLabel", background=tema.fundo, foreground=tema.texto)
    estilo.configure("Dica.TLabel", background=tema.fundo, foreground=tema.secundario)
    estilo.configure("TLabelframe", background=tema.fundo, bordercolor=tema.borda)
    estilo.configure("TLabelframe.Label", background=tema.fundo, foreground=tema.texto,
                     font=(tema.familia_destaque, 10))
    estilo.configure("TCheckbutton", background=tema.fundo, foreground=tema.texto)
    estilo.configure("TSeparator", background=tema.borda)

    estilo.configure("TEntry", fieldbackground=tema.superficie, foreground=tema.texto)
    estilo.configure("TCombobox", fieldbackground=tema.superficie, foreground=tema.texto)
    estilo.configure("TSpinbox", fieldbackground=tema.superficie, foreground=tema.texto)

    estilo.configure("TButton", background=tema.superficie, foreground=tema.texto, padding=(10, 5))
    estilo.map("TButton", background=[("pressed", tema.primaria), ("active", tema.ativo)],
               foreground=[("pressed", tema.texto_primaria)])

    estilo.configure("TNotebook", background=tema.fundo, bordercolor=tema.borda)
    estilo.configure("TNotebook.Tab", background=tema.fundo, foreground=tema.secundario, padding=(14, 6))
    estilo.map("TNotebook.Tab", background=[("selected", tema.superficie)],
               foreground=[("selected", tema.texto)], font=[("selected", (tema.familia_destaque, 10))])

    estilo.configure("Treeview", background=tema.superficie, fieldbackground=tema.superficie,
                     foreground=tema.texto, bordercolor=tema.borda, rowheight=24)
    estilo.map("Treeview", background=[("selected", tema.ativo)], foreground=[("selected", tema.texto)])
    estilo.configure("Treeview.Heading", background=tema.fundo, foreground=tema.texto,
                     font=(tema.familia_destaque, 10))

    raiz.configure(bg=tema.fundo)
    raiz.option_add("*Text.background", tema.superficie)
    raiz.option_add("*Text.foreground", tema.texto)
    raiz.option_add("*Listbox.background", tema.superficie)
    raiz.option_add("*Listbox.foreground", tema.texto)
    return tema
