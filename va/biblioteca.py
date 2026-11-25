"""Biblioteca de prints: guarda, lista e apaga os prints e seus ajustes, e exporta o codigo para o projeto."""

import shutil
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from va.export.generator import GUIA, codigo_servico, gerar_codigo, trecho_constantes
from va.export.storage import gravar_acao, gravar_metadado, ler_metadados, listar_modulos, offset_de, remover_acao
from va.paths import pasta_imagens


@dataclass(frozen=True)
class Exportacao:
    """O que foi copiado para o projeto e o que ja existia nele e foi mantido."""

    copiados: tuple[str, ...]
    ignorados: tuple[str, ...]


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

    def gerar_codigo(self) -> None:
        gerar_codigo(self.pasta_saida)

    def codigo_do_modulo(self, modulo: str) -> tuple[str, str]:
        """Classe de constantes da pagina e o arquivo src/services/<modulo>.py."""
        pasta = self.pasta_imagens / modulo
        nomes = sorted(arquivo.stem for arquivo in pasta.glob("*.png"))
        return trecho_constantes(modulo, nomes), codigo_servico(modulo, nomes, ler_metadados(pasta))

    def desvio_do_print(self, nome: str) -> tuple[int, int] | None:
        """Desvio proprio do print ('modulo/nome.png'), ou None se ele usa o desvio padrao."""
        caminho = self.caminho(nome)
        return offset_de(ler_metadados(caminho.parent).get(caminho.stem, {}))

    def definir_desvio(self, nome: str, dx: int | None, dy: int | None) -> None:
        """Grava o desvio proprio do print. Com dx ou dy None, o print volta ao desvio padrao."""
        caminho = self.caminho(nome)
        gravar_metadado(caminho.parent, caminho.stem, offset_x=dx, offset_y=dy)

    def exportar(self, destino: Path) -> Exportacao:
        """Copia para a pasta do projeto os prints e os servicos gerados.

        Nada que ja existe no projeto e substituido: esses arquivos aparecem em `ignorados`
        e precisam ser colados a mao (os metodos do servico, por exemplo).
        """
        origem = self.pasta_saida / "src"
        if not origem.exists():
            raise FileNotFoundError("Nada para exportar: capture um print primeiro.")
        copiados, ignorados = [], []
        arquivos = [*origem.glob("static/images/*/*.png"), *origem.glob("services/*.py")]
        for arquivo in arquivos:
            if arquivo.name == "__init__.py":
                continue
            relativo = arquivo.relative_to(origem)
            alvo = destino / "src" / relativo
            if alvo.exists():
                ignorados.append(relativo.as_posix())
                continue
            alvo.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(arquivo, alvo)
            copiados.append(relativo.as_posix())
        if not (destino / GUIA).exists():
            shutil.copy2(self.pasta_saida / GUIA, destino / GUIA)
        return Exportacao(tuple(sorted(copiados)), tuple(sorted(ignorados)))
