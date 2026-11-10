"""Gera o codigo estruturado a partir dos prints capturados.

Dentro da pasta de saida, copie a pasta src para o projeto:

    src/static/images/<modulo>/<nome>.png   prints capturados
    src/static/images/<modulo>/acoes.json   acao padrao de cada print
    src/template_constants.py               uma classe por modulo, um metodo por print
    src/automation/config.py                padroes da automacao (copia das Configuracoes)
    src/automation/perform_action.py        funcao perform_action() reutilizavel
    src/services/<modulo>.py                uma funcao de automacao por print
"""

import json
import keyword
import re
import unicodedata
from pathlib import Path

ACOES_DISPONIVEIS = ("clicar", "esperar")
ACOES_PADRAO = "clicar"
ARQUIVO_ACOES = "acoes.json"
NOMES_RESERVADOS = {"config", "perform_action", "template_constants", "__init__"}
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

MODELO_PERFORM_ACTION = '''"""Executa uma acao visual: acha a imagem na tela e age sobre ela.

Gerado pelo Visual Automator. Os padroes ficam em src/automation/config.py.
"""

import time
from pathlib import Path

import pyautogui
import pyscreeze

from src.automation.config import CONFIG_AUTOMACAO

RAIZ = Path(__file__).resolve().parents[2]
ACOES = ("clicar", "clicar_duplo", "clicar_direito", "esperar")

pyautogui.FAILSAFE = True  # mouse no canto superior esquerdo aborta


class ImagemNaoEncontrada(Exception):
    pass


def _localizar(caminho, regiao=None, confianca=None):
    nivel = CONFIG_AUTOMACAO["confianca"] if confianca is None else confianca
    niveis = [nivel, *CONFIG_AUTOMACAO["niveis_confianca_fallback"]]
    tela = pyautogui.screenshot(region=regiao)
    for valor in niveis:
        try:
            caixa = pyscreeze.locate(caminho, tela, confidence=valor, grayscale=CONFIG_AUTOMACAO["escala_cinza"])
        except pyscreeze.ImageNotFoundException:
            caixa = None
        if caixa is not None:
            x, y, largura, altura = (int(valor_caixa) for valor_caixa in caixa)
            if regiao is not None:
                x, y = x + regiao[0], y + regiao[1]
            return x, y, largura, altura
    return None


def perform_action(imagem, acao="clicar", timeout=None, regiao=None, confianca=None):
    """Localiza `imagem` (caminho relativo a raiz do projeto) e executa `acao`.

    Retorna o ponto (x, y) clicado, ou a caixa encontrada quando a acao e "esperar".
    Levanta ImagemNaoEncontrada se a imagem nao aparecer dentro do timeout.
    """
    if acao not in ACOES:
        raise ValueError(f"Acao desconhecida: {acao}")
    caminho = Path(imagem)
    if not caminho.is_absolute():
        caminho = RAIZ / caminho
    limite = time.monotonic() + (CONFIG_AUTOMACAO["timeout"] if timeout is None else timeout)
    caixa = _localizar(str(caminho), regiao, confianca)
    while caixa is None and time.monotonic() < limite:
        time.sleep(CONFIG_AUTOMACAO["intervalo"])
        caixa = _localizar(str(caminho), regiao, confianca)
    if caixa is None:
        raise ImagemNaoEncontrada(f"Imagem nao encontrada: {imagem}")
    if acao == "esperar":
        return caixa
    x = caixa[0] + caixa[2] // 2 + CONFIG_AUTOMACAO["offset_x"]
    y = caixa[1] + caixa[3] // 2 + CONFIG_AUTOMACAO["offset_y"]
    pyautogui.moveTo(x, y, duration=CONFIG_AUTOMACAO["duracao_movimento"])
    if acao == "clicar_duplo":
        pyautogui.doubleClick(x, y)
    elif acao == "clicar_direito":
        pyautogui.click(x, y, button="right")
    else:
        pyautogui.click(x, y)
    time.sleep(CONFIG_AUTOMACAO["pausa_entre_passos"])
    return x, y
'''


def pasta_imagens(pasta_saida: Path) -> Path:
    return pasta_saida / "src" / "static" / "images"


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
    _escrever(pasta_modulo / ARQUIVO_ACOES, json.dumps(acoes, indent=2, ensure_ascii=False))


def remover_acao(pasta_modulo: Path, nome: str) -> None:
    acoes = ler_acoes(pasta_modulo)
    if acoes.pop(nome, None) is not None:
        _escrever(pasta_modulo / ARQUIVO_ACOES, json.dumps(acoes, indent=2, ensure_ascii=False))


def gerar_codigo(pasta_saida: Path, config: dict) -> None:
    """Regenera todo o codigo a partir das pastas de imagens. Arquivos gerados sao sobrescritos."""
    raiz = pasta_imagens(pasta_saida)
    modulos = listar_modulos(pasta_saida)
    src = pasta_saida / "src"
    automacao = src / "automation"
    automacao.mkdir(parents=True, exist_ok=True)

    _escrever(src / "__init__.py", "")
    _escrever(automacao / "__init__.py", "")
    _escrever(automacao / "config.py", _codigo_config(config))
    _escrever(automacao / "perform_action.py", MODELO_PERFORM_ACTION)
    _escrever(src / "template_constants.py", _codigo_constantes(modulos))
    servicos = src / "services"
    _escrever(servicos / "__init__.py", "")
    for modulo, nomes in modulos.items():
        acoes = ler_acoes(raiz / modulo)
        _escrever(servicos / f"{modulo}.py", _codigo_automacao(modulo, nomes, acoes))


def _codigo_config(config: dict) -> str:
    linhas = [
        '"""Padroes da automacao. Gerado pelo Visual Automator.',
        "",
        "Para mudar estes valores, altere nas Configuracoes do app e exporte de novo.",
        '"""',
        "",
        "CONFIG_AUTOMACAO = {",
    ]
    for chave in CHAVES_AUTOMACAO:
        linhas.append(f"    {chave!r}: {config[chave]!r},")
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


def _escrever(caminho: Path, conteudo: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding="utf-8")
