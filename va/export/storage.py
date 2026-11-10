"""Leitura e escrita dos prints e das acoes padrao (acoes.json) na pasta de saida."""

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


def ler_acoes(pasta_modulo: Path) -> dict[str, str]:
    caminho = pasta_modulo / ARQUIVO_ACOES
    if not caminho.exists():
        return {}
    return json.loads(caminho.read_text(encoding="utf-8"))


def gravar_acao(pasta_modulo: Path, nome: str, acao: str) -> None:
    acoes = ler_acoes(pasta_modulo)
    acoes[nome] = acao
    escrever(pasta_modulo / ARQUIVO_ACOES, json.dumps(acoes, indent=2, ensure_ascii=False))


def remover_acao(pasta_modulo: Path, nome: str) -> None:
    acoes = ler_acoes(pasta_modulo)
    if acoes.pop(nome, None) is not None:
        escrever(pasta_modulo / ARQUIVO_ACOES, json.dumps(acoes, indent=2, ensure_ascii=False))


def escrever(caminho: Path, conteudo: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding="utf-8")
