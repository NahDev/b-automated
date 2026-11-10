"""Configuracoes do programa, salvas em config.json ao lado do programa."""

import json
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path

from va.paths import BASE_DIR

ARQUIVO_CONFIG = BASE_DIR / "config.json"


@dataclass(frozen=True)
class Settings:
    """Padroes de automacao e de pastas. Imutavel: mudancas viram uma nova instancia via `alterar`."""

    confianca: float = 0.8
    niveis_confianca_fallback: tuple[float, ...] = (0.7, 0.6)
    timeout: float = 10.0
    intervalo: float = 0.5
    escala_cinza: bool = True
    duracao_movimento: float = 0.2
    offset_x: int = 0
    offset_y: int = 0
    pausa_entre_passos: float = 0.3
    pasta_saida: str = "saida"
    pasta_tessdata: str = "tessdata"
    idioma_ocr: str = "por+eng"
    tesseract_cmd: str = ""

    @classmethod
    def carregar(cls, caminho: Path = ARQUIVO_CONFIG) -> "Settings":
        """Le o arquivo e completa com os padroes. Sem arquivo ou com JSON invalido, usa os padroes."""
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        nomes = {campo.name for campo in fields(cls)}
        valores = {chave: valor for chave, valor in dados.items() if chave in nomes}
        if "niveis_confianca_fallback" in valores:
            valores["niveis_confianca_fallback"] = tuple(valores["niveis_confianca_fallback"])
        return cls(**valores)

    def salvar(self, caminho: Path = ARQUIVO_CONFIG) -> None:
        caminho.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")

    def alterar(self, **campos) -> "Settings":
        return replace(self, **campos)
