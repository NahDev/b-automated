"""Nomes validos em Python a partir de textos livres digitados pelo usuario."""

import keyword
import re
import unicodedata

NOMES_RESERVADOS = {"config", "perform_action", "template_constants", "__init__"}


def identificador(texto: str) -> str:
    """Transforma um texto livre em nome valido de arquivo, funcao e variavel."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    nome = re.sub(r"\W+", "_", sem_acento.strip().lower()).strip("_")
    if not nome:
        raise ValueError("Informe um nome com letras ou numeros.")
    if nome[0].isdigit():
        nome = f"p_{nome}"
    if keyword.iskeyword(nome):
        nome = f"{nome}_"
    return nome


def identificador_modulo(texto: str) -> str:
    nome = identificador(texto)
    if nome in NOMES_RESERVADOS:
        nome = f"{nome}_pagina"
    return nome


def nome_classe(modulo: str) -> str:
    return "".join(parte.capitalize() for parte in modulo.split("_") if parte)
