"""Gera o codigo estruturado a partir dos prints capturados. Arquivos gerados sao sobrescritos.

Dentro da pasta de saida, copie a pasta src para o projeto:

    src/static/images/<modulo>/<nome>.png   prints capturados
    src/static/images/<modulo>/acoes.json   acao padrao de cada print
    src/template_constants.py               uma classe por modulo, um metodo por print
    src/automation/config.py                padroes da automacao (copia das Configuracoes)
    src/automation/perform_action.py        funcao perform_action() reutilizavel
    src/services/<modulo>.py                uma funcao de automacao por print
"""

from pathlib import Path

from va.export.naming import nome_classe
from va.export.storage import ACOES_DISPONIVEIS, ACOES_PADRAO, ler_acoes, listar_modulos, escrever
from va.export.template import MODELO_PERFORM_ACTION
from va.paths import pasta_imagens
from va.settings import Settings

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
    """Regenera todo o codigo a partir das pastas de imagens."""
    raiz = pasta_imagens(pasta_saida)
    modulos = listar_modulos(pasta_saida)
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
        acoes = ler_acoes(raiz / modulo)
        escrever(servicos / f"{modulo}.py", _codigo_automacao(modulo, nomes, acoes))


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
    linhas = ['"""Caminhos das imagens por modulo. Gerado pelo Visual Automator; nao edite."""']
    for modulo, nomes in modulos.items():
        linhas += ["", "", f"class {nome_classe(modulo)}:", f'    """Imagens do modulo {modulo}."""']
        for nome in nomes:
            linhas += [
                "",
                "    @staticmethod",
                f"    def {nome}() -> str:",
                f'        return "src/static/images/{modulo}/{nome}.png"',
            ]
    return "\n".join(linhas) + "\n"


def _codigo_automacao(modulo: str, nomes: list[str], acoes: dict[str, str]) -> str:
    classe = nome_classe(modulo)
    linhas = [
        f'"""Acoes do modulo {modulo}. Gerado pelo Visual Automator; nao edite."""',
        "",
        "from src.automation.perform_action import perform_action",
        f"from src.template_constants import {classe}",
    ]
    for nome in nomes:
        acao = acoes.get(nome, ACOES_PADRAO)
        if acao not in ACOES_DISPONIVEIS:
            acao = ACOES_PADRAO
        linhas += [
            "",
            "",
            f"def {acao}_{nome}(timeout=None):",
            f'    return perform_action({classe}.{nome}(), acao="{acao}", timeout=timeout)',
        ]
    return "\n".join(linhas) + "\n"
