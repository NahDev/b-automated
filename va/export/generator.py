"""Gera o codigo no padrao do projeto: constantes em src/configs/template_constants.py e servicos em src/services/.

Saida gerada dentro da pasta de saida (espelha a estrutura do projeto do dev):

    src/static/images/<modulo>/<nome>.png   prints capturados
    src/services/<modulo>.py                servico da pagina, um metodo por print
    INTEGRACAO.md                           classe de constantes de cada pagina e instrucoes

O template_constants.py do projeto nao e gerado: ele ja tem outras paginas. A classe de cada
pagina fica no guia e na janela de codigo, para colar no lugar certo.
"""

from pathlib import Path

from va.export.naming import classe_pagina, classe_servico
from va.export.storage import ACOES_DISPONIVEIS, ACOES_PADRAO, escrever, ler_metadados, listar_modulos, offset_de
from va.paths import pasta_imagens

GUIA = "INTEGRACAO.md"


def gerar_codigo(pasta_saida: Path) -> None:
    """Regenera os servicos e o guia de integracao a partir das pastas de imagens."""
    raiz = pasta_imagens(pasta_saida)
    modulos = listar_modulos(pasta_saida)
    metadados = {modulo: ler_metadados(raiz / modulo) for modulo in modulos}
    for modulo, nomes in modulos.items():
        escrever(pasta_saida / "src" / "services" / f"{modulo}.py", codigo_servico(modulo, nomes, metadados[modulo]))
    escrever(pasta_saida / GUIA, guia_integracao(modulos, metadados))


def trecho_constantes(modulo: str, nomes: list[str]) -> str:
    """Classe de constantes da pagina, para colar em src/configs/template_constants.py."""
    linhas = [f"class {classe_pagina(modulo)}(_BasePaths):", f'    """Caminhos para imagens da pagina {modulo}."""']
    for nome in nomes:
        linhas += ["", f'    {nome.upper()} = _BasePaths.BASE_DIR / "{modulo}" / "{nome}.png"']
    return "\n".join(linhas) + "\n"


def codigo_servico(modulo: str, nomes: list[str], metadados: dict[str, dict]) -> str:
    """Arquivo src/services/<modulo>.py no padrao dos servicos do projeto."""
    constantes = classe_pagina(modulo)
    metodos: list[list[str]] = []
    libs: set[str] = set()
    for funcao, nome, acao in funcoes_do_modulo(nomes, metadados):
        metodo, usados = _metodo(funcao, f"{constantes}.{nome.upper()}", acao, offset_de(metadados.get(nome, {})))
        metodos.append(metodo)
        libs |= usados

    linhas = [
        f'"""Acoes da pagina {modulo}. Gerado pelo Visual Automator."""',
        "",
        f"from src.configs.template_constants import {constantes}",
    ]
    if libs:
        linhas.append(f"from src.libs.automation import {', '.join(sorted(libs))}")
    linhas += ["", "", f"class {classe_servico(modulo)}:", f'    """Acoes da pagina {modulo}."""']
    for metodo in metodos:
        linhas += ["", *metodo]
    return "\n".join(linhas) + "\n"


def funcoes_do_modulo(nomes: list[str], metadados: dict[str, dict]) -> list[tuple[str, str, str]]:
    """Trios (metodo, print, acao): `clicar_botao_entrar`, `botao_entrar`, `clicar`."""
    trios = []
    for nome in nomes:
        acao = metadados.get(nome, {}).get("acao", ACOES_PADRAO)
        if acao not in ACOES_DISPONIVEIS:
            acao = ACOES_PADRAO
        trios.append((f"{acao}_{nome}", nome, acao))
    return trios


def _metodo(funcao: str, alvo: str, acao: str, desvio: tuple[int, int] | None) -> tuple[list[str], set[str]]:
    """Metodo do servico para um print, e os nomes de src.libs.automation que ele usa."""
    if acao == "esperar":
        linhas = [f"    def {funcao}(self, max_attempts=10):", f"        return find_element(template_path={alvo}, max_attempts=max_attempts)"]
        return linhas, {"find_element"}
    if desvio is not None:
        comando, usados = f"ClickOffsetCommand(dx={desvio[0]}, dy={desvio[1]})", {"perform_action", "ClickOffsetCommand"}
    else:
        comando, usados = "ClickCommand()", {"perform_action", "ClickCommand"}
    return [f"    def {funcao}(self):", f"        perform_action(template_name={alvo}, command={comando})"], usados


def guia_integracao(modulos: dict[str, list[str]], metadados: dict[str, dict[str, dict]]) -> str:
    """Markdown com o passo a passo para colar o codigo gerado no projeto."""
    linhas = [
        "# Integracao do codigo gerado",
        "",
        "Gerado pelo Visual Automator. Cole cada parte no lugar indicado do projeto.",
        "",
        "## Passo a passo",
        "",
        "1. Copie `src/static/images/<modulo>/` para o projeto. O botao **Exportar projeto...** faz isso e nao substitui arquivos que ja existem.",
        "2. Cole a classe de cada pagina em `src/configs/template_constants.py`, depois da classe `_BasePaths`.",
        "3. Crie `src/services/<modulo>.py` com o arquivo gerado. Se o servico ja existir, cole os metodos dentro da classe existente.",
        "",
        "## Paginas",
        "",
    ]
    if not modulos:
        linhas += ["Nenhum print capturado ainda.", ""]
    for modulo, nomes in modulos.items():
        linhas += [f"### `{modulo}`", "", "Classe de constantes (`src/configs/template_constants.py`):", "", "```python"]
        linhas += [trecho_constantes(modulo, nomes).rstrip(), "```", ""]
        linhas += [f"Servico (`src/services/{modulo}.py`): classe `{classe_servico(modulo)}`.", ""]
        if nomes:
            primeiro = funcoes_do_modulo(nomes, metadados[modulo])[0][0]
            linhas += [
                "Uso:",
                "",
                "```python",
                f"from src.services.{modulo} import {classe_servico(modulo)}",
                "",
                f"{classe_servico(modulo)}().{primeiro}()",
                "```",
                "",
            ]
    linhas += ["## Dependencias", "", "O servico usa `src/libs/automation.py` do proprio projeto. Nada novo precisa ser instalado.", ""]
    return "\n".join(linhas)
