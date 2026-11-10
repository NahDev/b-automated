"""Busca de ocorrencias de um print dentro de uma captura de tela. Nao depende de interface."""

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


@dataclass(frozen=True)
class Ocorrencia:
    x: int
    y: int
    largura: int
    altura: int
    confianca: float

    @property
    def centro(self) -> tuple[int, int]:
        return self.x + self.largura // 2, self.y + self.altura // 2


def buscar_ocorrencias(
    tela: Image.Image,
    caminho: Path,
    confianca: float,
    escala_cinza: bool = True,
    limite: int = 50,
) -> tuple[list[Ocorrencia], Ocorrencia | None]:
    """Acha todas as ocorrencias do print em `tela` com confianca >= `confianca`.

    Devolve (ocorrencias, melhor). As ocorrencias vao da mais parecida para a menos.
    `melhor` e a melhor semelhanca mesmo abaixo do limite; None se o print nao couber
    na tela ou nao tiver variacao para comparar.
    """
    modo = "L" if escala_cinza else "RGB"
    imagem_tela = np.array(tela.convert(modo))
    alvo = np.array(Image.open(caminho).convert(modo))
    altura, largura = alvo.shape[:2]
    if altura > imagem_tela.shape[0] or largura > imagem_tela.shape[1] or alvo.std() == 0:
        return [], None

    res = cv2.matchTemplate(imagem_tela, alvo, cv2.TM_CCOEFF_NORMED)
    res = np.nan_to_num(res, nan=0.0, posinf=0.0, neginf=0.0)
    y_melhor, x_melhor = np.unravel_index(np.argmax(res), res.shape)
    melhor = Ocorrencia(int(x_melhor), int(y_melhor), largura, altura, float(res[y_melhor, x_melhor]))

    ys, xs = np.where(res >= confianca)
    candidatos = sorted(zip(res[ys, xs].tolist(), xs.tolist(), ys.tolist()), reverse=True)
    escolhidas: list[Ocorrencia] = []
    for score, x, y in candidatos:
        # Descarta posicoes que se sobrepoem a uma ocorrencia ja escolhida (mesmo botao)
        if all(abs(x - o.x) >= largura / 2 or abs(y - o.y) >= altura / 2 for o in escolhidas):
            escolhidas.append(Ocorrencia(x, y, largura, altura, score))
            if len(escolhidas) == limite:
                break
    return escolhidas, melhor
