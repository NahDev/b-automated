"""Gera o codigo Python de um roteiro, para o dev colar no projeto.

Cada passo vira uma linha equivalente:
- prints viram `perform_action` com a constante do modulo (ex: `Login.BOTAO_ENTRAR`);
- digitar, teclas e esperas viram chamadas de `pyautogui` e `time`.

Passos que dependem do OCR do app (clicar_texto, esperar_texto) nao tem equivalente no projeto:
ficam como comentario e sao devolvidos em `nao_exportados`, para o app avisar o usuario.
"""

from dataclasses import dataclass

from va.automation.runner import Passo
from va.export.naming import identificador, nome_classe


@dataclass(frozen=True)
class CodigoRoteiro:
    codigo: str
    nao_exportados: tuple[str, ...]


@dataclass(frozen=True)
class _Linha:
    texto: str
    imports: frozenset[str] = frozenset()
    classe: str | None = None  # classe de template_constants usada por esta linha


def codigo_roteiro(passos: list[Passo], nome: str) -> CodigoRoteiro:
    """Funcao `roteiro_<nome>` com os passos em ordem. Levanta ValueError se o nome for invalido."""
    funcao = f"roteiro_{identificador(nome)}"
    corpo: list[str] = []
    nao_exportados: list[str] = []
    imports: set[str] = set()
    classes: set[str] = set()
    for passo in passos:
        linha = _traduzir(passo)
        if linha is None:
            descricao = _descrever(passo)
            nao_exportados.append(descricao)
            corpo.append(f"    # nao exportado (depende do app): {descricao}")
            continue
        imports |= linha.imports
        if linha.classe is not None:
            classes.add(linha.classe)
        corpo += [f"    {trecho}" for trecho in linha.texto.split("\n")]
    if not corpo:
        corpo = ["    pass"]
    return CodigoRoteiro(_montar(funcao, corpo, imports, classes), tuple(nao_exportados))


def _montar(funcao: str, corpo: list[str], imports: set[str], classes: set[str]) -> str:
    biblioteca_padrao = ["import time"] if "time" in imports else []
    terceiros = [f"import {modulo}" for modulo in ("pyautogui", "pyperclip") if modulo in imports]
    locais = []
    if "perform_action" in imports:
        locais.append("from src.automation.perform_action import perform_action")
    locais += [f"from src.template_constants import {classe}" for classe in sorted(classes)]

    blocos = ['"""Roteiro gerado pelo Visual Automator. Nao edite: gere de novo pela aba Roteiro."""']
    blocos += ["\n".join(grupo) for grupo in (biblioteca_padrao, terceiros, locais) if grupo]
    cabecalho = "\n\n".join(blocos)
    return f'{cabecalho}\n\n\ndef {funcao}(timeout=None):\n    """Passos do roteiro {funcao}."""\n' + "\n".join(corpo) + "\n"


def _traduzir(passo: Passo) -> _Linha | None:
    if passo.acao in ("clicar_imagem", "esperar_imagem"):
        return _linha_imagem(passo)
    if passo.acao == "digitar":
        texto = passo.valor or passo.alvo
        if texto.isascii():
            return _Linha(f"pyautogui.write({texto!r}, interval=0.02)", frozenset({"pyautogui"}))
        return _Linha(
            f"pyperclip.copy({texto!r})\npyautogui.hotkey('ctrl', 'v')",
            frozenset({"pyautogui", "pyperclip"}),
        )
    if passo.acao == "tecla":
        teclas = [parte.strip() for parte in passo.alvo.split("+") if parte.strip()]
        if not teclas:
            return None
        return _Linha(f"pyautogui.hotkey({', '.join(repr(tecla) for tecla in teclas)})", frozenset({"pyautogui"}))
    if passo.acao == "esperar_segundos":
        try:
            segundos = float(passo.valor or passo.alvo)
        except ValueError:
            return None
        return _Linha(f"time.sleep({segundos!r})", frozenset({"time"}))
    return None


def _linha_imagem(passo: Passo) -> _Linha | None:
    partes = passo.alvo.split("/")
    if len(partes) != 2 or not partes[1].endswith(".png"):
        return None
    modulo, arquivo = partes
    nome = arquivo[: -len(".png")]
    acao = "clicar" if passo.acao == "clicar_imagem" else "esperar"
    classe = nome_classe(modulo)
    return _Linha(
        f'perform_action({classe}.{nome.upper()}, acao="{acao}", timeout=timeout)',
        frozenset({"perform_action"}),
        classe,
    )


def _descrever(passo: Passo) -> str:
    descricao = f"{passo.acao} '{passo.alvo}'"
    return f"{descricao} valor '{passo.valor}'" if passo.valor else descricao
