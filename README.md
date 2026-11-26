# Visual Automator

App desktop estilo SikuliX para automação e testes de interface, feito com pyautogui, OpenCV e pytesseract. Funciona no Windows.

Testado com Python 3.14 no Windows 11.

## O que tem

- **Capturar:** tire prints de uma região da tela (botão ou F9). Cada print vai para um módulo (página) com nome e ação padrão.
- **Código gerado no padrão do projeto:** cada página vira `src/services/<modulo>.py`, com uma classe `<Modulo>Service` e um método por print, usando `src.libs.automation` (`perform_action`, `ClickCommand`, `ClickOffsetCommand`, `find_element`). A classe de constantes `<Modulo>Page(_BasePaths)` vai para o `INTEGRACAO.md`, para colar em `src/configs/template_constants.py`.
- **Desvio por print no código:** o desvio próprio de um print vira `ClickOffsetCommand(dx, dy)` no método dele.
- **Exportar projeto...:** copia para a pasta do projeto os prints e os serviços que ainda não existem. Arquivos que já existem não são substituídos e aparecem numa lista. **Código do módulo...** mostra a classe de constantes e o arquivo do serviço, com botões de copiar.
- **Testar na tela e medir:** ficam na aba Laboratório. "Testar na tela" mostra as ocorrências do print. "Medir ancorado" pede o quadrado do print e o ponto do clique na tela congelada, e calcula o desvio a partir do centro do quadrado.
- **Roteiro:** monta passos (clicar imagem, clicar texto, esperar imagem ou texto, digitar, tecla, esperar segundos), salva e abre em JSON e executa. "Gerar codigo do roteiro" mostra a função Python equivalente para colar no projeto. Passos de OCR (clicar texto, esperar texto) não têm equivalente no projeto: ficam de fora e são listados no aviso.
- **Laboratório:** ajusta o desvio do clique (dx, dy), com a cruz no centro do print. Cada print pode ter desvio próprio ("Salvar desvio deste print"); quem não tem usa o desvio padrão. O desvio próprio vai para o código gerado (`perform_action(..., offset=(dx, dy))`) e vale também para o roteiro e para o teste na tela.
- **Configurações:** padrões de confiança, tempos de espera, desvios, pastas, idioma do OCR e tema visual. Ficam em `config.json`.
- **Temas:** o padrão é o **btime** (cores do design system, fonte Branding). O tema **neutro** usa azul e cinza. Troque em **Configurações > Tema visual** e reinicie o programa. O código dos temas fica em `va/ui/temas.py`; para criar outro, copie um `Tema` e ajuste as cores.

## Instalação

### 1. Python

Instale o Python 3.14 pelo site python.org ou pela Microsoft Store. Depois confira se o launcher `py` responde:

```bash
py -3.14 --version
```

Se o comando abrir a Microsoft Store em vez de mostrar a versão, use o caminho completo do `python.exe` instalado nos comandos abaixo.

### 2. Tesseract (para o OCR)

Baixe o instalador para Windows em https://github.com/UB-Mannheim/tesseract/wiki e instale na pasta padrão `C:\Program Files\Tesseract-OCR`. O app encontra o programa sozinho nessa pasta. Se você instalar em outro lugar, informe o caminho do `tesseract.exe` na aba **Configurações**.

Os idiomas `por` e `eng` já vêm na pasta `tessdata` deste repositório, então não precisa instalar pacotes de idioma.

### 3. Código e dependências

```bash
git clone git@github.com:NahDev/b-automated.git
cd b-automated
py -3.14 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Não é preciso ativar o venv: os comandos usam o Python dele diretamente.

## Como rodar

```bash
.venv\Scripts\python.exe app.py
```

Para abrir sem a janela do console, use `.venv\Scripts\pythonw.exe app.py`.

Para interromper uma automação, mova o mouse para o canto superior esquerdo da tela (FailSafe do pyautogui).

## Testes

```bash
.venv\Scripts\python.exe -m pytest
```

O teste de OCR é pulado se o Tesseract não for encontrado.

## Gerar o executável (.exe)

```bash
.venv\Scripts\python.exe -m pip install -r requirements-build.txt
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

O resultado fica em `dist\VisualAutomator\`. Ele inclui o Tesseract e os idiomas, então pode ser copiado para outro PC e aberto sem instalar nada. Esse build exige o Tesseract instalado em `C:\Program Files\Tesseract-OCR` na máquina onde você gera o executável.

## Solução de problemas

- **"Tesseract não encontrado" ou OCR não acha texto:** confira se o Tesseract está em `C:\Program Files\Tesseract-OCR` ou ajuste o caminho em **Configurações**.
- **Erros:** o detalhe fica em `logs\visual_automator.log`, ao lado do programa.
- **A janela abre em outra posição:** é o comportamento normal do Windows. Confira a tela antes de clicar em botões.
- **`python` abre a Microsoft Store:** o Windows usa um atalho que não é o Python. Use `py -3.14` ou o caminho completo do `python.exe` instalado.
- **Antivírus bloqueia o `.exe`:** é comum com automação de mouse e teclado. Libere o programa no antivírus ou assine o executável.

## Estrutura

O código é dividido em camadas. A interface (`va/ui`) só chama os serviços; a regra de negócio não depende do Tkinter.

- `app.py`: ponto de entrada.
- `va/settings.py`: configurações imutáveis, salvas em `config.json`.
- `va/automation/`: busca de imagens e textos (`vision.py`, `tesseract.py`), ações de clique e teclado (`actions.py`) e execução de roteiros (`runner.py`).
- `va/export/`: geração do código em `saida/` (`generator.py`), nomes válidos (`naming.py`), leitura e escrita dos prints e das ações (`storage.py`).
- `va/biblioteca.py`: guarda, lista e apaga os prints.
- `va/geometria.py`: cálculos de escala e de desvio, sem interface.
- `va/ui/`: telas Tkinter. `app.py` monta as abas; cada aba fica em seu arquivo.
- `va/logs.py`, `va/paths.py`: log em arquivo e pastas do programa (funcionam também no `.exe`).
- `tessdata/`: idiomas do OCR (`eng` e `por`).
- `tests/`: testes por camada. Rodam sem abrir a janela, exceto pela checagem de interface.
- `build_exe.ps1`: gera o executável com PyInstaller.
