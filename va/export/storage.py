"""Leitura e escrita dos prints e de seus ajustes (acoes.json) na pasta de saida.

acoes.json guarda, por print, um dicionario com a "acao" (clicar ou esperar) e, se o print tiver
desvio proprio, "offset_x" e "offset_y". Arquivos antigos, que guardam so a acao como texto,
continuam sendo lidos.
"""

import json
from pathlib import Path

from va.paths import pasta_imagens

ACOES_DISPONIVEIS = ("clicar", "esperar")
ACOES_PADRAO = "clicar"
ARQUIVO_ACOES = "acoes.json"


def listar_modulos(pasta_saida: Path) -> dict[str, list[str]]:
    """Mapeia cada modulo (pasta) para os nomes dos seus prints, sem a extensao."""
    raiz = pasta_imagens(pasta_saida)
    raiz.mkdir(parents=True, exist_ok=True)
    return {
        pasta.name: sorted(arquivo.stem for arquivo in pasta.glob("*.png"))
        for pasta in sorted(raiz.iterdir())
        if pasta.is_dir()
    }


def ler_metadados(pasta_modulo: Path) -> dict[str, dict]:
    """Ajustes de cada print do modulo: {"botao": {"acao": "clicar", "offset_x": 5, "offset_y": 0}}."""
    caminho = pasta_modulo / ARQUIVO_ACOES
    if not caminho.exists():
        return {}
    bruto = json.loads(caminho.read_text(encoding="utf-8"))
    return {nome: {"acao": valor} if isinstance(valor, str) else dict(valor) for nome, valor in bruto.items()}


def ler_acoes(pasta_modulo: Path) -> dict[str, str]:
    return {nome: meta.get("acao", ACOES_PADRAO) for nome, meta in ler_metadados(pasta_modulo).items()}


def offset_de(meta: dict) -> tuple[int, int] | None:
    """Desvio proprio do print, ou None se ele usa o desvio padrao."""
    dx, dy = meta.get("offset_x"), meta.get("offset_y")
    if dx is None or dy is None:
        return None
    return int(dx), int(dy)


def gravar_metadado(pasta_modulo: Path, nome: str, **campos) -> None:
    """Atualiza os campos de um print. Valor None remove o campo."""
    dados = ler_metadados(pasta_modulo)
    meta = dados.get(nome, {})
    for chave, valor in campos.items():
        if valor is None:
            meta.pop(chave, None)
        else:
            meta[chave] = valor
    dados[nome] = meta
    _escrever_dados(pasta_modulo, dados)


def gravar_acao(pasta_modulo: Path, nome: str, acao: str) -> None:
    gravar_metadado(pasta_modulo, nome, acao=acao)


def remover_acao(pasta_modulo: Path, nome: str) -> None:
    dados = ler_metadados(pasta_modulo)
    if dados.pop(nome, None) is not None:
        _escrever_dados(pasta_modulo, dados)


def _escrever_dados(pasta_modulo: Path, dados: dict[str, dict]) -> None:
    escrever(pasta_modulo / ARQUIVO_ACOES, json.dumps(dados, indent=2, ensure_ascii=False))


def escrever(caminho: Path, conteudo: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding="utf-8")
