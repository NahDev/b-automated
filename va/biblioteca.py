"""Biblioteca de prints: guarda, lista e apaga os prints e suas acoes padrao, na pasta de saida."""

from pathlib import Path

from PIL import Image

from va.export.generator import gerar_codigo
from va.export.storage import gravar_acao, listar_modulos, remover_acao
from va.paths import pasta_imagens
from va.settings import Settings


class Biblioteca:
    def __init__(self, pasta_saida: Path):
        self.pasta_saida = pasta_saida
        self.pasta_imagens = pasta_imagens(pasta_saida)
        self.pasta_imagens.mkdir(parents=True, exist_ok=True)

    def nomes(self) -> list[str]:
        """Prints no formato 'modulo/nome.png', em ordem."""
        return sorted(
            f"{pasta.name}/{arquivo.name}"
            for pasta in self.pasta_imagens.iterdir()
            if pasta.is_dir()
            for arquivo in pasta.glob("*.png")
        )

    def modulos(self) -> list[str]:
        return sorted(listar_modulos(self.pasta_saida))

    def caminho(self, nome: str) -> Path:
        return self.pasta_imagens / nome

    def existe(self, modulo: str, nome: str) -> bool:
        return self.caminho(f"{modulo}/{nome}.png").exists()

    def salvar(self, imagem: Image.Image, modulo: str, nome: str, acao: str) -> Path:
        pasta_modulo = self.pasta_imagens / modulo
        pasta_modulo.mkdir(parents=True, exist_ok=True)
        destino = pasta_modulo / f"{nome}.png"
        imagem.save(destino)
        gravar_acao(pasta_modulo, nome, acao)
        return destino

    def excluir(self, nome: str) -> None:
        caminho = self.caminho(nome)
        caminho.unlink()
        remover_acao(caminho.parent, caminho.stem)

    def gerar_codigo(self, settings: Settings) -> None:
        gerar_codigo(self.pasta_saida, settings)
