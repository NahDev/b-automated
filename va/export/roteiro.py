"""Gera o codigo Python de um roteiro no padrao do projeto (API de src/libs/automation.py).

Cada passo vira uma chamada da API do projeto:
- clicar/esperar imagem: perform_action ou find_element com a constante da pagina (ex: CheckOrderPage.BOTAO).
  Se o print tem desvio proprio, o clique usa ClickOffsetCommand com esse desvio;
- digitar: writer (aceita acentos); tecla: press_key, ou pyautogui.hotkey para combinacoes;
- esperar_segundos: time.sleep.

Passos de OCR (clicar_texto, esperar_texto) nao tem equivalente no projeto: ficam como comentario
e sao devolvidos em `nao_exportados`.
"""

from dataclasses import dataclass

from va.automation.runner import Passo
from va.export.naming import classe_pagina, identificador

# Tipos de importacao usados pelos passos: ("libs", nome), ("constantes", classe),
# ("excecao", nome), ("modulo", nome) para `import nome`.
Importacao = tuple[str, str]


@dataclass(frozen=True)
class CodigoRoteiro:
    codigo: str
    nao_exportados: tuple[str, ...]


@dataclass(frozen=True)
class _Linha:
    texto: str
    importacoes: frozenset[Importacao] = frozenset()


def codigo_roteiro(
    passos: list[Passo], nome: str, desvios: dict[str, tuple[int, int]] | None = None
) -> CodigoRoteiro:
    """Funcao `roteiro_<nome>` com os passos em ordem.

    `desvios` mapeia o alvo de um passo ('modulo/nome.png') para o desvio proprio do print.
    Levanta ValueError se o nome for invalido.
    """
    desvios = desvios or {}
    funcao = f"roteiro_{identificador(nome)}"
    corpo: list[str] = []
    nao_exportados: list[str] = []
    importacoes: set[Importacao] = set()
    for passo in passos:
        linha = _traduzir(passo, desvios.get(passo.alvo))
        if linha is None:
            descricao = _descrever(passo)
            nao_exportados.append(descricao)
            corpo.append(f"    # nao exportado (depende do app): {descricao}")
            continue
        importacoes |= linha.importacoes
        corpo += [f"    {trecho}" for trecho in linha.texto.split("\n")]
    if not corpo:
        corpo = ["    pass"]
    return CodigoRoteiro(_montar(funcao, corpo, importacoes), tuple(nao_exportados))


def _montar(funcao: str, corpo: list[str], importacoes: set[Importacao]) -> str:
    padrao = [f"import {nome}" for tipo, nome in sorted(importacoes) if tipo == "modulo" and nome == "time"]
    terceiros = [f"import {nome}" for tipo, nome in sorted(importacoes) if tipo == "modulo" and nome == "pyautogui"]
    locais = []
    classes = sorted(nome for tipo, nome in importacoes if tipo == "constantes")
    if classes:
        locais.append(f"from src.configs.template_constants import {', '.join(classes)}")
    if ("excecao", "ElementNotFound") in importacoes:
        locais.append("from src.exceptions.exceptions import ElementNotFound")
    libs = sorted(nome for tipo, nome in importacoes if tipo == "libs")
    if libs:
        locais.append(f"from src.libs.automation import {', '.join(libs)}")

    blocos = ['"""Roteiro gerado pelo Visual Automator. Nao edite: gere de novo pela aba Roteiro."""']
    blocos += ["\n".join(grupo) for grupo in (padrao, terceiros, locais) if grupo]
    cabecalho = "\n\n".join(blocos)
    return f'{cabecalho}\n\n\ndef {funcao}(timeout=None):\n    """Passos do roteiro {funcao}."""\n' + "\n".join(corpo) + "\n"


def _traduzir(passo: Passo, desvio: tuple[int, int] | None) -> _Linha | None:
    if passo.acao in ("clicar_imagem", "esperar_imagem"):
        return _linha_imagem(passo, desvio)
    if passo.acao == "digitar":
        texto = passo.valor or passo.alvo
        return _Linha(f"writer({texto!r})", frozenset({("libs", "writer")}))
    if passo.acao == "tecla":
        teclas = [parte.strip() for parte in passo.alvo.split("+") if parte.strip()]
        if not teclas:
            return None
        if len(teclas) == 1:
            return _Linha(f"press_key({teclas[0]!r})", frozenset({("libs", "press_key")}))
        return _Linha(f"pyautogui.hotkey({', '.join(repr(tecla) for tecla in teclas)})", frozenset({("modulo", "pyautogui")}))
    if passo.acao == "esperar_segundos":
        try:
            segundos = float(passo.valor or passo.alvo)
        except ValueError:
            return None
        return _Linha(f"time.sleep({segundos!r})", frozenset({("modulo", "time")}))
    return None


def _linha_imagem(passo: Passo, desvio: tuple[int, int] | None) -> _Linha | None:
    partes = passo.alvo.split("/")
    if len(partes) != 2 or not partes[1].endswith(".png"):
        return None
    modulo, arquivo = partes
    alvo = f"{classe_pagina(modulo)}.{arquivo[: -len('.png')].upper()}"
    importacoes = {("constantes", classe_pagina(modulo))}

    if passo.acao == "esperar_imagem":
        mensagem = f"Imagem nao apareceu: {passo.alvo}"
        texto = f"if not find_element(template_path={alvo}):\n    raise ElementNotFound({mensagem!r})"
        importacoes |= {("libs", "find_element"), ("excecao", "ElementNotFound")}
        return _Linha(texto, frozenset(importacoes))

    if desvio is not None:
        comando = f"ClickOffsetCommand(dx={desvio[0]}, dy={desvio[1]})"
        importacoes |= {("libs", "perform_action"), ("libs", "ClickOffsetCommand")}
    else:
        comando = "ClickCommand()"
        importacoes |= {("libs", "perform_action"), ("libs", "ClickCommand")}
    return _Linha(f"perform_action(template_name={alvo}, command={comando})", frozenset(importacoes))


def _descrever(passo: Passo) -> str:
    descricao = f"{passo.acao} '{passo.alvo}'"
    return f"{descricao} valor '{passo.valor}'" if passo.valor else descricao
