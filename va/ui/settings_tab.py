"""Aba Configuracoes: edita os padroes de automacao. Os campos sao descritos em CAMPOS."""

import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from va.settings import Settings

if TYPE_CHECKING:
    from va.ui.app import App


@dataclass(frozen=True)
class Campo:
    chave: str
    titulo: str
    dica: str
    tipo: str  # "float", "int", "bool", "lista" (valores separados por virgula) ou "texto"


CAMPOS = (
    Campo("confianca", "Confianca padrao (0 a 1)", "Quanto maior, mais parecido o alvo precisa estar. Ex: 0.8", "float"),
    Campo("niveis_confianca_fallback", "Tolerancias extras", "Usadas se a padrao nao achar. Separe por virgula. Ex: 0.7, 0.6", "lista"),
    Campo("timeout", "Tempo maximo de espera (s)", "Quanto tempo procurar o alvo antes de desistir", "float"),
    Campo("intervalo", "Intervalo entre buscas (s)", "Pausa entre uma tentativa e a proxima", "float"),
    Campo("escala_cinza", "Comparar em tons de cinza", "Mais tolerante a mudancas de cor ou tema", "bool"),
    Campo("duracao_movimento", "Duracao do movimento do mouse (s)", "Tempo que o mouse leva ate o alvo", "float"),
    Campo("offset_x", "Deslocamento X do clique (px)", "Somado ao centro do alvo", "int"),
    Campo("offset_y", "Deslocamento Y do clique (px)", "Somado ao centro do alvo", "int"),
    Campo("pausa_entre_passos", "Pausa entre passos (s)", "Respiro depois de cada passo do roteiro", "float"),
    Campo("pasta_saida", "Pasta de saida do codigo", "Relativa a pasta do programa. Ex: saida", "texto"),
    Campo("pasta_tessdata", "Pasta dos idiomas do OCR", "Relativa a pasta do programa. Ex: tessdata", "texto"),
    Campo("idioma_ocr", "Idioma do OCR", "Ex: por, eng ou por+eng", "texto"),
    Campo("tesseract_cmd", "Caminho do tesseract.exe", "Deixe vazio se ele estiver no PATH", "texto"),
)


def texto_do_valor(valor) -> str:
    if isinstance(valor, (list, tuple)):
        return ", ".join(str(item) for item in valor)
    return str(valor)


def ler_valor(campo: Campo, variavel: tk.Variable):
    """Converte o texto digitado no tipo do campo. Levanta ValueError se estiver invalido."""
    if campo.tipo == "bool":
        return bool(variavel.get())
    if campo.tipo == "lista":
        return tuple(float(item) for item in str(variavel.get()).split(",") if item.strip())
    if campo.tipo == "int":
        return int(variavel.get())
    if campo.tipo == "float":
        return float(variavel.get())
    return str(variavel.get()).strip()


class ConfigTab(ttk.Frame):
    def __init__(self, master: tk.Misc, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._variaveis: dict[str, tk.Variable] = {}
        self._montar()
        self.mostrar(app.settings)

    def _montar(self) -> None:
        quadro = ttk.Frame(self)
        quadro.pack(fill="both", expand=True)
        for linha, campo in enumerate(CAMPOS):
            ttk.Label(quadro, text=campo.titulo).grid(row=linha, column=0, sticky="w", padx=4, pady=4)
            if campo.tipo == "bool":
                variavel: tk.Variable = tk.BooleanVar()
                ttk.Checkbutton(quadro, variable=variavel).grid(row=linha, column=1, sticky="w")
            else:
                variavel = tk.StringVar()
                ttk.Entry(quadro, textvariable=variavel, width=32).grid(row=linha, column=1, sticky="w")
            ttk.Label(quadro, text=campo.dica, foreground="gray").grid(row=linha, column=2, sticky="w", padx=8)
            self._variaveis[campo.chave] = variavel

        botoes = ttk.Frame(quadro)
        botoes.grid(row=len(CAMPOS), column=0, columnspan=3, sticky="w", pady=14)
        ttk.Button(botoes, text="Salvar configuracoes", command=self.salvar).pack(side="left", padx=4)
        ttk.Button(botoes, text="Restaurar padroes", command=lambda: self.mostrar(Settings())).pack(side="left", padx=4)

    def mostrar(self, settings: Settings) -> None:
        """Preenche os campos com os valores de `settings`."""
        for campo in CAMPOS:
            valor = getattr(settings, campo.chave)
            variavel = self._variaveis[campo.chave]
            variavel.set(valor if campo.tipo == "bool" else texto_do_valor(valor))

    def salvar(self) -> None:
        try:
            alteracoes = {campo.chave: ler_valor(campo, self._variaveis[campo.chave]) for campo in CAMPOS}
        except ValueError as erro:
            messagebox.showerror("Valor invalido", f"Confira os campos numericos.\n\n{erro}", parent=self.app)
            return
        self.app.aplicar_settings(self.app.settings.alterar(**alteracoes))
        self.app.registrar("Configuracoes salvas em config.json.")
