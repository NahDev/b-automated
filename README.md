# Visual Automator

App desktop estilo SikuliX para automação e testes de interface, feito com pyautogui, OpenCV e pytesseract. Funciona no Windows.

Testado com Python 3.14 no Windows 11.

## O que tem

- **Capturar:** tire prints de uma região da tela (botão ou F9). Cada print vai para um módulo (página) com nome e ação padrão.
- **Código gerado:** a pasta `saida/src` recebe `template_constants.py`, `automation/perform_action.py`, `automation/config.py` e `services/<modulo>.py`, prontos para copiar para outro projeto.
- **Testar na tela:** mostra todas as ocorrências do print, com índice e confiança. Você escolhe uma para clicar e pode ajustar a confiança.
- **Roteiro:** monta passos (clicar imagem, clicar texto, esperar imagem ou texto, digitar, tecla, esperar segundos), salva e abre em JSON e executa.
- **Laboratório:** ajusta o desvio padrão do clique (dx, dy). Mede o desvio com dois cliques na tela.
- **Configurações:** padrões de confiança, tempos de espera, desvios, pastas e idioma do OCR. Ficam em `config.json`.

## Instalação

### 1. Python

Instale o Python 3.14 pelo site python.org ou pela Microsoft Store. Marque a opção **Add python.exe to PATH** na instalação.

### 2. Tesseract (para o OCR)

Baixe o instalador para Windows em https://github.com/UB-Mannheim/tesseract/wiki e instale na pasta padrão `C:\Program Files\Tesseract-OCR`. O app encontra o programa sozinho nessa pasta. Se você instalar em outro lugar, informe o caminho do `tesseract.exe` na aba **Configurações**.

Os idiomas `por` e `eng` já vêm na pasta `tessdata` deste repositório, então não precisa instalar pacotes de idioma.

### 3. Código e dependências

```bash
git clone <URL-DO-REPOSITORIO>
cd visual_automator
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Como rodar

```bash
python app.py
```

Para abrir sem a janela do console, use `pythonw app.py`.

Para interromper uma automação, mova o mouse para o canto superior esquerdo da tela (FailSafe do pyautogui).

## Testes

```bash
pytest
```

O teste de OCR é pulado se o Tesseract não for encontrado.

## Gerar o executável (.exe)

```bash
pip install -r requirements-build.txt
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

O resultado fica em `dist\VisualAutomator\`. Ele inclui o Tesseract e os idiomas, então pode ser copiado para outro PC e aberto sem instalar nada. Esse build exige o Tesseract instalado em `C:\Program Files\Tesseract-OCR` na máquina onde você gera o executável.

## Solução de problemas

- **"Tesseract não encontrado" ou OCR não acha texto:** confira se o Tesseract está em `C:\Program Files\Tesseract-OCR` ou ajuste o caminho em **Configurações**.
- **Erros:** o detalhe fica em `logs\visual_automator.log`, ao lado do programa.
- **A janela abre em outra posição:** é o comportamento normal do Windows. Confira a tela antes de clicar em botões.
- **Antivírus bloqueia o `.exe`:** é comum com automação de mouse e teclado. Libere o programa no antivírus ou assine o executável.

## Estrutura

- `app.py`: interface principal.
- `captura.py`, `janela_teste.py`, `laboratorio.py`: telas de captura, teste de localização e laboratório.
- `core.py`: busca por imagem e por texto, cliques e digitação.
- `exportador.py`: geração do código estruturado em `saida/`.
- `config.py`, `registro.py`: configurações padrão e log em arquivo.
- `tessdata/`: idiomas do OCR (`eng` e `por`).
- `tests/`: testes automatizados.
