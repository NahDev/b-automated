"""Janelas auxiliares, sempre centralizadas na tela: nome do print e avisos rapidos."""

import tkinter as tk
from tkinter import messagebox, ttk

from va.export.naming import identificador, identificador_modulo
from va.export.storage import ACOES_DISPONIVEIS
from va.geometria import posicao_centralizada


def centralizar(janela: tk.Toplevel) -> None:
    janela.update_idletasks()
    x, y = posicao_centralizada(
        janela.winfo_reqwidth(), janela.winfo_reqheight(), janela.winfo_screenwidth(), janela.winfo_screenheight()
    )
    janela.geometry(f"+{x}+{y}")


def pedir_dados_print(master: tk.Misc, modulos: list[str], ultimo_modulo: str) -> tuple[str, str, str] | None:
    """Pergunta modulo, nome e acao padrao do print, no centro da tela. Devolve None se cancelar."""
    resultado: dict[str, tuple[str, str, str]] = {}
    janela = tk.Toplevel(master)
    janela.title("Salvar print")
    janela.transient(master)
    janela.resizable(False, False)
    var_modulo = tk.StringVar(value=ultimo_modulo)
    var_nome = tk.StringVar()
    var_acao = tk.StringVar(value=ACOES_DISPONIVEIS[0])

    quadro = ttk.Frame(janela, padding=18)
    quadro.pack(fill="both", expand=True)
    ttk.Label(quadro, text="Modulo (pagina)").grid(row=0, column=0, sticky="w", pady=4)
    ttk.Combobox(quadro, textvariable=var_modulo, values=modulos, width=30).grid(row=0, column=1, sticky="we", padx=(8, 0))
    ttk.Label(quadro, text="Nome do print").grid(row=1, column=0, sticky="w", pady=4)
    entrada_nome = ttk.Entry(quadro, textvariable=var_nome, width=32)
    entrada_nome.grid(row=1, column=1, sticky="we", padx=(8, 0))
    ttk.Label(quadro, text="Acao padrao").grid(row=2, column=0, sticky="w", pady=4)
    ttk.Combobox(quadro, textvariable=var_acao, values=ACOES_DISPONIVEIS, state="readonly", width=30).grid(
        row=2, column=1, sticky="we", padx=(8, 0)
    )

    def confirmar(_evento=None) -> None:
        try:
            modulo = identificador_modulo(var_modulo.get())
            nome = identificador(var_nome.get())
        except ValueError as erro:
            messagebox.showwarning("Nome invalido", str(erro), parent=janela)
            return
        resultado["dados"] = (modulo, nome, var_acao.get())
        janela.destroy()

    def cancelar(_evento=None) -> None:
        janela.destroy()

    botoes = ttk.Frame(quadro)
    botoes.grid(row=3, column=0, columnspan=2, sticky="e", pady=(14, 0))
    ttk.Button(botoes, text="Cancelar", command=cancelar).pack(side="right", padx=(6, 0))
    ttk.Button(botoes, text="Salvar", command=confirmar).pack(side="right")
    janela.bind("<Return>", confirmar)
    janela.bind("<Escape>", cancelar)
    centralizar(janela)
    janela.wait_visibility()
    janela.grab_set()
    entrada_nome.focus_set()
    master.wait_window(janela)
    return resultado.get("dados")


def aviso_temporario(master: tk.Misc, texto: str, ms: int = 1800) -> None:
    """Pop-up pequeno no centro da tela que some sozinho."""
    janela = tk.Toplevel(master)
    janela.overrideredirect(True)
    janela.attributes("-topmost", True)
    ttk.Label(janela, text=texto, font=("Segoe UI", 12, "bold"), padding=20).pack()
    centralizar(janela)
    janela.after(ms, janela.destroy)
