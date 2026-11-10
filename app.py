"""Aplicativo desktop: tire prints dos alvos, monte roteiros e rode as automacoes."""

import ctypes
import json
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pyautogui
from PIL import Image, ImageTk

from captura import medir_desvio, selecionar_regiao
from janela_teste import JanelaTesteLocalizacao
from registro import ARQUIVO_LOG, logger
from registro import configurar as configurar_registro
from config import BASE_DIR, PADROES, carregar, salvar
from core import ACOES, Automador, ElementoNaoEncontrado
from exportador import (
    ACOES_DISPONIVEIS,
    gerar_codigo,
    gravar_acao,
    identificador,
    identificador_modulo,
    listar_modulos,
    remover_acao,
)
from laboratorio import AbaLaboratorio

DESCRICAO = {
    "confianca": ("Confianca padrao (0 a 1)", "Quanto maior, mais parecido o alvo precisa estar. Ex: 0.8"),
    "niveis_confianca_fallback": ("Tolerancias extras", "Usadas se a padrao nao achar. Separe por virgula. Ex: 0.7, 0.6"),
    "timeout": ("Tempo maximo de espera (s)", "Quanto tempo procurar o alvo antes de desistir"),
    "intervalo": ("Intervalo entre buscas (s)", "Pausa entre uma tentativa e a proxima"),
    "escala_cinza": ("Comparar em tons de cinza", "Mais tolerante a mudancas de cor ou tema"),
    "duracao_movimento": ("Duracao do movimento do mouse (s)", "Tempo que o mouse leva ate o alvo"),
    "offset_x": ("Deslocamento X do clique (px)", "Somado ao centro do alvo"),
    "offset_y": ("Deslocamento Y do clique (px)", "Somado ao centro do alvo"),
    "pausa_entre_passos": ("Pausa entre passos (s)", "Respiro depois de cada passo do roteiro"),
    "pasta_saida": ("Pasta de saida do codigo", "Relativa a pasta do programa. Ex: saida"),
    "pasta_tessdata": ("Pasta dos idiomas do OCR", "Relativa a pasta do programa. Ex: tessdata"),
    "idioma_ocr": ("Idioma do OCR", "Ex: por, eng ou por+eng"),
    "tesseract_cmd": ("Caminho do tesseract.exe", "Deixe vazio se ele estiver no PATH"),
}


def _texto_valor(valor) -> str:
    if isinstance(valor, list):
        return ", ".join(str(item) for item in valor)
    return str(valor)


def _ler_valor(chave: str, var):
    padrao = PADROES[chave]
    if isinstance(padrao, bool):
        return bool(var.get())
    if isinstance(padrao, list):
        return [float(item) for item in str(var.get()).split(",") if item.strip()]
    if isinstance(padrao, int):
        return int(var.get())
    if isinstance(padrao, float):
        return float(var.get())
    return str(var.get()).strip()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Visual Automator")
        self.geometry("1000x680")
        self.minsize(860, 560)

        self.config_atual = carregar()
        self.automador = Automador(self.config_atual)
        self.automador.pasta_imagens.mkdir(parents=True, exist_ok=True)

        self.passos: list[dict] = []
        self.fila_log: queue.Queue = queue.Queue()
        self.parar_flag = threading.Event()
        self.thread_execucao: threading.Thread | None = None
        self.nomes_imagens: list[str] = []
        self.ultimo_modulo = ""
        self.foto_preview = None

        self.bind("<F9>", lambda _evento: self.capturar())

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.aba_captura = ttk.Frame(notebook, padding=10)
        self.aba_roteiro = ttk.Frame(notebook, padding=10)
        self.aba_config = ttk.Frame(notebook, padding=10)
        notebook.add(self.aba_captura, text="Capturar")
        notebook.add(self.aba_roteiro, text="Roteiro")
        notebook.add(self.aba_config, text="Configuracoes")

        self._montar_captura()
        self._montar_roteiro()
        self._montar_config()
        self.aba_lab = AbaLaboratorio(
            notebook,
            pasta_imagens=lambda: self.automador.pasta_imagens,
            desvio_atual=lambda: (self.config_atual["offset_x"], self.config_atual["offset_y"]),
            ao_salvar_desvio=self._salvar_desvio_padrao,
            medir_na_tela=self._medir_desvio_na_tela,
        )
        notebook.add(self.aba_lab, text="Laboratorio")
        self.atualizar_lista()
        self.after(100, self._drenar_log)

    # ---------- aba Capturar
    def _montar_captura(self):
        topo = ttk.Frame(self.aba_captura)
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

        corpo = ttk.Frame(self.aba_captura)
        corpo.pack(fill="both", expand=True)

        esquerda = ttk.Frame(corpo)
        esquerda.pack(side="left", fill="y")
        ttk.Label(esquerda, text="Imagens capturadas").pack(anchor="w")
        self.lista = tk.Listbox(esquerda, width=34, exportselection=False)
        self.lista.pack(fill="y", expand=True)
        self.lista.bind("<<ListboxSelect>>", lambda _evento: self._mostrar_selecionada())

        botoes = ttk.Frame(esquerda)
        botoes.pack(fill="x", pady=6)
        ttk.Button(botoes, text="Testar na tela", command=self.testar_selecionada).pack(fill="x", pady=2)
        ttk.Button(botoes, text="Adicionar ao roteiro", command=self.adicionar_selecionada_ao_roteiro).pack(fill="x", pady=2)
        ttk.Button(botoes, text="Excluir", command=self.excluir_selecionada).pack(fill="x", pady=2)
        ttk.Button(botoes, text="Atualizar lista", command=self.atualizar_lista).pack(fill="x", pady=2)
        ttk.Button(botoes, text="Abrir pasta de saida", command=self.abrir_pasta_saida).pack(fill="x", pady=2)

        direita = ttk.LabelFrame(corpo, text="Visualizacao", padding=10)
        direita.pack(side="left", fill="both", expand=True, padx=(12, 0))
        self.label_preview = ttk.Label(direita, text="Selecione uma imagem")
        self.label_preview.pack(expand=True)

    def capturar(self):
        self.withdraw()
        self.after(300, lambda: selecionar_regiao(self, self._apos_captura))

    def _apos_captura(self, imagem: Image.Image | None):
        self.deiconify()
        if imagem is None:
            return
        dados = self._formulario_captura()
        if dados is None:
            return
        modulo, nome, acao = dados
        pasta_modulo = self.automador.pasta_imagens / modulo
        destino = pasta_modulo / f"{nome}.png"
        if destino.exists() and not messagebox.askyesno(
            "Substituir", f"'{modulo}/{nome}.png' ja existe. Substituir?", parent=self
        ):
            return
        pasta_modulo.mkdir(parents=True, exist_ok=True)
        imagem.save(destino)
        gravar_acao(pasta_modulo, nome, acao)
        self.ultimo_modulo = modulo
        self._gerar_codigo()
        self.atualizar_lista(selecionar=f"{modulo}/{nome}.png")
        self.log(f"Print salvo: {destino}")

    def _formulario_captura(self) -> tuple[str, str, str] | None:
        """Pergunta modulo, nome e acao padrao do print. Retorna None se cancelar."""
        modulos = sorted(listar_modulos(self.automador.pasta_saida))
        resultado = {}
        janela = tk.Toplevel(self)
        janela.title("Salvar captura")
        janela.transient(self)
        janela.resizable(False, False)
        var_modulo = tk.StringVar(value=self.ultimo_modulo)
        var_nome = tk.StringVar()
        var_acao = tk.StringVar(value=ACOES_DISPONIVEIS[0])

        quadro = ttk.Frame(janela, padding=14)
        quadro.pack(fill="both", expand=True)
        ttk.Label(quadro, text="Modulo (pagina)").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Combobox(quadro, textvariable=var_modulo, values=modulos, width=30).grid(
            row=0, column=1, sticky="we", padx=(8, 0)
        )
        ttk.Label(quadro, text="Nome do print").grid(row=1, column=0, sticky="w", pady=4)
        entrada_nome = ttk.Entry(quadro, textvariable=var_nome, width=32)
        entrada_nome.grid(row=1, column=1, sticky="we", padx=(8, 0))
        ttk.Label(quadro, text="Acao padrao").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Combobox(
            quadro, textvariable=var_acao, values=ACOES_DISPONIVEIS, state="readonly", width=30
        ).grid(row=2, column=1, sticky="we", padx=(8, 0))

        def confirmar(_evento=None):
            try:
                modulo = identificador_modulo(var_modulo.get())
                nome = identificador(var_nome.get())
            except ValueError as erro:
                messagebox.showwarning("Nome invalido", str(erro), parent=janela)
                return
            resultado["dados"] = (modulo, nome, var_acao.get())
            janela.destroy()

        def cancelar(_evento=None):
            janela.destroy()

        botoes = ttk.Frame(quadro)
        botoes.grid(row=3, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(botoes, text="Cancelar", command=cancelar).pack(side="right", padx=(6, 0))
        ttk.Button(botoes, text="Salvar", command=confirmar).pack(side="right")
        janela.bind("<Return>", confirmar)
        janela.bind("<Escape>", cancelar)
        janela.wait_visibility()
        janela.grab_set()
        entrada_nome.focus_set()
        self.wait_window(janela)
        return resultado.get("dados")

    def _medir_desvio_na_tela(self, ao_concluir):
        self.withdraw()
        self.after(300, lambda: medir_desvio(self, lambda desvio: self._fim_medicao(desvio, ao_concluir)))

    def _fim_medicao(self, desvio, ao_concluir):
        self.deiconify()
        if desvio is not None:
            ao_concluir(*desvio)

    def report_callback_exception(self, exc, val, tb):
        """Erros de botoes e eventos da interface caem aqui: registra e avisa o usuario."""
        logger.error("Erro na interface", exc_info=(exc, val, tb))
        messagebox.showerror("Erro", f"{val}\n\nDetalhes em:\n{ARQUIVO_LOG}", parent=self)

    def _salvar_desvio_padrao(self, dx: int, dy: int):
        config = carregar()
        config.update(offset_x=dx, offset_y=dy)
        salvar(config)
        self.config_atual = carregar()
        self.automador = Automador(self.config_atual)
        if "offset_x" in self.vars_config:
            self.vars_config["offset_x"].set(str(dx))
            self.vars_config["offset_y"].set(str(dy))
        self._gerar_codigo()
        self.log(f"Desvio padrao salvo: dx={dx}, dy={dy}")

    def _gerar_codigo(self):
        try:
            gerar_codigo(self.automador.pasta_saida, self.config_atual)
        except OSError as erro:
            self.log(f"Falha ao gerar o codigo: {erro}")

    def abrir_pasta_saida(self):
        pasta = self.automador.pasta_saida
        pasta.mkdir(parents=True, exist_ok=True)
        os.startfile(pasta)

    def atualizar_lista(self, selecionar: str | None = None):
        raiz = self.automador.pasta_imagens
        raiz.mkdir(parents=True, exist_ok=True)
        self.nomes_imagens = sorted(
            f"{pasta.name}/{arquivo.name}"
            for pasta in raiz.iterdir()
            if pasta.is_dir()
            for arquivo in pasta.glob("*.png")
        )
        self.lista.delete(0, tk.END)
        for nome in self.nomes_imagens:
            self.lista.insert(tk.END, nome)
        if selecionar in self.nomes_imagens:
            indice = self.nomes_imagens.index(selecionar)
            self.lista.selection_set(indice)
            self._mostrar_selecionada()
        self.aba_lab.atualizar_imagens(self.nomes_imagens, selecionar)

    def _nome_selecionado(self) -> str | None:
        selecao = self.lista.curselection()
        return self.nomes_imagens[selecao[0]] if selecao else None

    def _mostrar_selecionada(self):
        nome = self._nome_selecionado()
        if nome is None:
            return
        with Image.open(self.automador.pasta_imagens / nome) as imagem:
            miniatura = imagem.copy()
        miniatura.thumbnail((560, 420))
        self.foto_preview = ImageTk.PhotoImage(miniatura)
        self.label_preview.configure(image=self.foto_preview, text="")

    def testar_selecionada(self):
        nome = self._nome_selecionado()
        if nome is None:
            return
        JanelaTesteLocalizacao(self, nome, self._salvar_confianca_padrao)

    def _salvar_confianca_padrao(self, confianca: float):
        config = carregar()
        config["confianca"] = confianca
        salvar(config)
        self.config_atual = carregar()
        self.automador = Automador(self.config_atual)
        if "confianca" in self.vars_config:
            self.vars_config["confianca"].set(str(confianca))
        self._gerar_codigo()
        self.log(f"Confianca padrao salva: {confianca:.2f}")

    def adicionar_selecionada_ao_roteiro(self):
        nome = self._nome_selecionado()
        if nome is None:
            return
        self.adicionar_passo("clicar_imagem", nome, "")

    def excluir_selecionada(self):
        nome = self._nome_selecionado()
        if nome is None:
            return
        if not messagebox.askyesno("Excluir", f"Excluir a imagem '{nome}'?", parent=self):
            return
        caminho = self.automador.pasta_imagens / nome
        caminho.unlink()
        remover_acao(caminho.parent, caminho.stem)
        self._gerar_codigo()
        self.atualizar_lista()
        self.label_preview.configure(image="", text="Selecione uma imagem")

    # ---------- aba Roteiro
    def _montar_roteiro(self):
        formulario = ttk.LabelFrame(self.aba_roteiro, text="Novo passo", padding=8)
        formulario.pack(fill="x")

        self.var_acao = tk.StringVar(value=ACOES[0])
        self.var_alvo = tk.StringVar()
        self.var_valor = tk.StringVar()

        ttk.Label(formulario, text="Acao").grid(row=0, column=0, sticky="w")
        ttk.Combobox(formulario, textvariable=self.var_acao, values=ACOES, state="readonly", width=20).grid(row=1, column=0, padx=(0, 8), sticky="w")
        ttk.Label(formulario, text="Alvo (imagem, texto ou tecla)").grid(row=0, column=1, sticky="w")
        ttk.Entry(formulario, textvariable=self.var_alvo, width=34).grid(row=1, column=1, padx=(0, 8), sticky="we")
        ttk.Label(formulario, text="Valor (texto a digitar ou segundos)").grid(row=0, column=2, sticky="w")
        ttk.Entry(formulario, textvariable=self.var_valor, width=28).grid(row=1, column=2, padx=(0, 8), sticky="we")
        ttk.Button(formulario, text="Adicionar", command=self._adicionar_do_formulario).grid(row=1, column=3)
        formulario.columnconfigure(1, weight=1)

        meio = ttk.Frame(self.aba_roteiro)
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

        controles = ttk.Frame(self.aba_roteiro)
        controles.pack(fill="x")
        tk.Button(
            controles, text="Executar", command=self.executar, bg="#16a34a", fg="white",
            font=("Segoe UI", 12, "bold"), relief="flat", width=14,
        ).pack(side="left")
        tk.Button(
            controles, text="Parar", command=self.parar, bg="#dc2626", fg="white",
            font=("Segoe UI", 12, "bold"), relief="flat", width=10,
        ).pack(side="left", padx=8)
        ttk.Label(controles, text="Mouse no canto superior esquerdo interrompe tudo.", foreground="gray").pack(side="left", padx=8)

        self.texto_log = tk.Text(self.aba_roteiro, height=8, state="disabled", wrap="word")
        self.texto_log.pack(fill="both", expand=False, pady=(8, 0))

    def adicionar_passo(self, acao: str, alvo: str, valor: str):
        self.passos.append({"acao": acao, "alvo": alvo, "valor": valor})
        self._recarregar_tabela()

    def _adicionar_do_formulario(self):
        acao = self.var_acao.get()
        alvo = self.var_alvo.get().strip()
        valor = self.var_valor.get().strip()
        if not alvo and acao != "digitar":
            messagebox.showwarning("Campo vazio", "Informe o alvo do passo.", parent=self)
            return
        if not alvo and not valor:
            messagebox.showwarning("Campo vazio", "Informe o texto a digitar.", parent=self)
            return
        self.adicionar_passo(acao, alvo, valor)
        self.var_alvo.set("")
        self.var_valor.set("")

    def _recarregar_tabela(self):
        self.tabela.delete(*self.tabela.get_children())
        for indice, passo in enumerate(self.passos):
            self.tabela.insert("", tk.END, iid=str(indice), values=(passo["acao"], passo["alvo"], passo["valor"]))

    def _indice_selecionado(self) -> int | None:
        selecao = self.tabela.selection()
        return int(selecao[0]) if selecao else None

    def remover_passo(self):
        indice = self._indice_selecionado()
        if indice is not None:
            del self.passos[indice]
            self._recarregar_tabela()

    def mover_passo(self, direcao: int):
        indice = self._indice_selecionado()
        if indice is None:
            return
        destino = indice + direcao
        if 0 <= destino < len(self.passos):
            self.passos[indice], self.passos[destino] = self.passos[destino], self.passos[indice]
            self._recarregar_tabela()
            self.tabela.selection_set(str(destino))

    def limpar_roteiro(self):
        if self.passos and messagebox.askyesno("Limpar", "Apagar todos os passos do roteiro?", parent=self):
            self.passos.clear()
            self._recarregar_tabela()

    def salvar_roteiro(self):
        caminho = filedialog.asksaveasfilename(
            parent=self, initialdir=BASE_DIR, defaultextension=".json",
            filetypes=[("Roteiro JSON", "*.json")],
        )
        if caminho:
            with open(caminho, "w", encoding="utf-8") as arquivo:
                json.dump({"passos": self.passos}, arquivo, indent=2, ensure_ascii=False)
            self.log(f"Roteiro salvo: {caminho}")

    def abrir_roteiro(self):
        caminho = filedialog.askopenfilename(
            parent=self, initialdir=BASE_DIR, filetypes=[("Roteiro JSON", "*.json")],
        )
        if caminho:
            with open(caminho, encoding="utf-8") as arquivo:
                self.passos = json.load(arquivo)["passos"]
            self._recarregar_tabela()
            self.log(f"Roteiro carregado: {caminho}")

    def executar(self):
        if self.thread_execucao and self.thread_execucao.is_alive():
            return
        if not self.passos:
            messagebox.showinfo("Roteiro vazio", "Adicione passos antes de executar.", parent=self)
            return
        self.parar_flag.clear()
        self.thread_execucao = threading.Thread(target=self._rodar, args=(list(self.passos),), daemon=True)
        self.thread_execucao.start()

    def parar(self):
        self.parar_flag.set()

    def _rodar(self, passos: list[dict]):
        """Roda em outra thread. Nada de Tk aqui: so fila de log."""
        self.fila_log.put("--- Inicio ---")
        for numero, passo in enumerate(passos, 1):
            if self.parar_flag.is_set():
                self.fila_log.put("Parado pelo usuario.")
                break
            try:
                self.automador.executar(passo["acao"], passo["alvo"], passo["valor"])
                self.fila_log.put(f"{numero}. OK: {passo['acao']} {passo['alvo']}")
                logger.info("Passo %d OK: %s %s", numero, passo["acao"], passo["alvo"])
            except ElementoNaoEncontrado as erro:
                self.fila_log.put(f"{numero}. FALHOU: {erro}")
                logger.warning("Passo %d FALHOU: %s", numero, erro)
                break
            except pyautogui.FailSafeException:
                self.fila_log.put("Interrompido: mouse no canto superior esquerdo (FailSafe).")
                logger.warning("Interrompido pelo FailSafe no passo %d", numero)
                break
            except Exception as erro:
                self.fila_log.put(f"{numero}. ERRO: {erro}")
                logger.exception("Passo %d com erro", numero)
                break
        self.fila_log.put("--- Fim ---")

    def _drenar_log(self):
        while True:
            try:
                self.log(self.fila_log.get_nowait())
            except queue.Empty:
                break
        self.after(100, self._drenar_log)

    def log(self, mensagem: str):
        self.texto_log.configure(state="normal")
        self.texto_log.insert(tk.END, mensagem + "\n")
        self.texto_log.see(tk.END)
        self.texto_log.configure(state="disabled")

    # ---------- aba Configuracoes
    def _montar_config(self):
        self.vars_config: dict[str, tk.Variable] = {}
        quadro = ttk.Frame(self.aba_config)
        quadro.pack(fill="both", expand=True)

        for linha, chave in enumerate(PADROES):
            titulo, dica = DESCRICAO[chave]
            ttk.Label(quadro, text=titulo).grid(row=linha, column=0, sticky="w", padx=4, pady=4)
            if isinstance(PADROES[chave], bool):
                var = tk.BooleanVar(value=self.config_atual[chave])
                ttk.Checkbutton(quadro, variable=var).grid(row=linha, column=1, sticky="w")
            else:
                var = tk.StringVar(value=_texto_valor(self.config_atual[chave]))
                ttk.Entry(quadro, textvariable=var, width=32).grid(row=linha, column=1, sticky="w")
            ttk.Label(quadro, text=dica, foreground="gray").grid(row=linha, column=2, sticky="w", padx=8)
            self.vars_config[chave] = var

        botoes = ttk.Frame(quadro)
        botoes.grid(row=len(PADROES), column=0, columnspan=3, sticky="w", pady=14)
        ttk.Button(botoes, text="Salvar configuracoes", command=self.salvar_config).pack(side="left", padx=4)
        ttk.Button(botoes, text="Restaurar padroes", command=self.restaurar_padroes).pack(side="left", padx=4)

    def salvar_config(self):
        try:
            nova = {chave: _ler_valor(chave, var) for chave, var in self.vars_config.items()}
        except ValueError as erro:
            messagebox.showerror("Valor invalido", f"Confira os campos numericos.\n\n{erro}", parent=self)
            return
        salvar(nova)
        self.config_atual = carregar()
        self.automador = Automador(self.config_atual)
        self.automador.pasta_imagens.mkdir(parents=True, exist_ok=True)
        self.atualizar_lista()
        self._gerar_codigo()
        self.log("Configuracoes salvas em config.json.")

    def restaurar_padroes(self):
        for chave, var in self.vars_config.items():
            if isinstance(PADROES[chave], bool):
                var.set(PADROES[chave])
            else:
                var.set(_texto_valor(PADROES[chave]))


def _ativar_dpi():
    """Sem isso, no Windows com escala (125%, 150%) as coordenadas do print e do clique nao batem."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        pass


if __name__ == "__main__":
    _ativar_dpi()
    configurar_registro()
    logger.info("Visual Automator iniciado")
    App().mainloop()
