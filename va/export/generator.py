"""Gera o codigo estruturado a partir dos prints capturados. Arquivos gerados sao sobrescritos.

Estrutura gerada dentro da pasta de saida (e o que o dev copia para o projeto):

    src/static/images/<modulo>/<nome>.png   prints capturados
    src/static/images/<modulo>/acoes.json   acao padrao de cada print
    src/template_constants.py               uma classe por modulo; uma constante por print
    src/automation/config.py                padroes da automacao (copia das Configuracoes)
    src/automation/perform_action.py        funcao perform_action() reutilizavel
    src/services/<modulo>.py                uma funcao por print, chamando perform_action direto
    INTEGRACAO.md                           onde colar cada arquivo e como usar
"""

from pathlib import Path

from va.export.naming import nome_classe
from va.export.storage import ACOES_DISPONIVEIS, ACOES_PADRAO, escrever, ler_acoes, listar_modulos
from va.export.template import MODELO_PERFORM_ACTION
from va.paths import pasta_imagens
from va.settings import Settings

GUIA = "INTEGRACAO.md"
CABECALHO_CONSTANTES = '"""Caminhos das imagens por modulo. Gerado pelo Visual Automator; nao edite."""'
CHAVES_AUTOMACAO = (
    "confianca",
    "niveis_confianca_fallback",
    "timeout",
    "intervalo",
    "escala_cinza",
    "duracao_movimento",
    "offset_x",
    "offset_y",
    "pausa_entre_passos",
)


def gerar_codigo(pasta_saida: Path, settings: Settings) -> None:
    """Regenera todo o codigo e o guia de integracao a partir das pastas de imagens."""
    raiz = pasta_imagens(pasta_saida)
    modulos = listar_modulos(pasta_saida)
    acoes = {modulo: ler_acoes(raiz / modulo) for modulo in modulos}
    src = pasta_saida / "src"
    automacao = src / "automation"
    servicos = src / "services"

    escrever(src / "__init__.py", "")
    escrever(automacao / "__init__.py", "")
    escrever(automacao / "config.py", _codigo_config(settings))
    escrever(automacao / "perform_action.py", MODELO_PERFORM_ACTION)
    escrever(src / "template_constants.py", _codigo_constantes(modulos))
    escrever(servicos / "__init__.py", "")
    for modulo, nomes in modulos.items():
        escrever(servicos / f"{modulo}.py", codigo_servico(modulo, nomes, acoes[modulo]))
    escrever(pasta_saida / GUIA, guia_integracao(modulos, acoes))


def trecho_constantes(modulo: str, nomes: list[str]) -> str:
    """So a classe de um modulo, para colar dentro de src/template_constants.py."""
    return _linhas_classe(modulo, nomes) + "\n"


def codigo_servico(modulo: str, nomes: list[str], acoes: dict[str, str]) -> str:
    """Arquivo src/services/<modulo>.py: cada print vira uma funcao que chama perform_action."""
    classe = nome_classe(modulo)
    linhas = [
        f'"""Acoes da pagina {modulo}. Gerado pelo Visual Automator; atualize pelo app, nao edite."""',
        "",
        "from src.automation.perform_action import perform_action",
        f"from src.template_constants import {classe}",
    ]
    for funcao, nome, acao in funcoes_do_modulo(nomes, acoes):
        linhas += [
            "",
            "",
            f"def {funcao}(timeout=None):",
            f'    return perform_action({classe}.{nome.upper()}, acao="{acao}", timeout=timeout)',
        ]
    return "\n".join(linhas) + "\n"


def funcoes_do_modulo(nomes: list[str], acoes: dict[str, str]) -> list[tuple[str, str, str]]:
    """Trios (funcao, print, acao): `clicar_botao_entrar`, `botao_entrar`, `clicar`."""
    trios = []
    for nome in nomes:
        acao = acoes.get(nome, ACOES_PADRAO)
        if acao not in ACOES_DISPONIVEIS:
            acao = ACOES_PADRAO
        trios.append((f"{acao}_{nome}", nome, acao))
    return trios


def guia_integracao(modulos: dict[str, list[str]], acoes: dict[str, dict[str, str]]) -> str:
    """Markdown com onde colar cada arquivo e como chamar as funcoes geradas."""
    linhas = [
        "# Integracao do codigo gerado",
        "",
        "Gerado pelo Visual Automator. Nao edite estes arquivos no projeto: ajuste no app e exporte de novo.",
        "",
        "## Onde colar",
        "",
        "Copie a pasta `src/` para a raiz do seu projeto. Se ela ja existir, substitua os arquivos abaixo:",
        "",
        "| Arquivo | O que fazer |",
        "|---|---|",
        "| `src/static/images/` | Copiar a pasta inteira. Os prints ficam aqui. |",
        "| `src/automation/config.py` | Substituir pelo arquivo gerado. |",
        "| `src/automation/perform_action.py` | Substituir pelo arquivo gerado. |",
        "| `src/template_constants.py` | Substituir pelo arquivo gerado. Ou colar so a classe do modulo (botao Copiar no app). |",
        "| `src/services/<modulo>.py` | Um arquivo por pagina. Criar se nao existir; substituir se ja existir. |",
        "",
        "## Dependencias",
        "",
        "```bash",
        "pip install pyautogui opencv-python pillow pyscreeze",
        "```",
        "",
        "## Modulos e funcoes",
        "",
    ]
    if not modulos:
        linhas += ["Nenhum print capturado ainda.", ""]
    for modulo, nomes in modulos.items():
        linhas += [f"### `{modulo}` -> `src/services/{modulo}.py`", ""]
        if not nomes:
            linhas += ["_Sem prints._", ""]
        for funcao, nome, _acao in funcoes_do_modulo(nomes, acoes[modulo]):
            linhas.append(f"- `{funcao}(timeout=None)`: usa `src/static/images/{modulo}/{nome}.png`")
        if nomes:
            linhas.append("")

    if modulos and any(modulos.values()):
        modulo = next(m for m, nomes in modulos.items() if nomes)
        funcao, _nome, _acao = funcoes_do_modulo(modulos[modulo], acoes[modulo])[0]
        linhas += [
            "## Uso",
            "",
            "```python",
            f"from src.services.{modulo} import {funcao}",
            "",
            f"{funcao}()  # localiza o print na tela e executa a acao",
            "```",
            "",
        ]
    return "\n".join(linhas)


def _codigo_config(settings: Settings) -> str:
    linhas = [
        '"""Padroes da automacao. Gerado pelo Visual Automator.',
        "",
        "Para mudar estes valores, altere nas Configuracoes do app e exporte de novo.",
        '"""',
        "",
        "CONFIG_AUTOMACAO = {",
    ]
    for chave in CHAVES_AUTOMACAO:
        linhas.append(f"    {chave!r}: {getattr(settings, chave)!r},")
    linhas.append("}")
    return "\n".join(linhas) + "\n"


def _codigo_constantes(modulos: dict[str, list[str]]) -> str:
    blocos = [_linhas_classe(modulo, nomes) for modulo, nomes in modulos.items()]
    return "\n\n\n".join([CABECALHO_CONSTANTES, *blocos]) + "\n"


def _linhas_classe(modulo: str, nomes: list[str]) -> str:
    linhas = [f"class {nome_classe(modulo)}:", f'    """Imagens do modulo {modulo}."""']
    for nome in nomes:
        linhas += ["", f'    {nome.upper()} = "src/static/images/{modulo}/{nome}.png"']
    return "\n".join(linhas)
