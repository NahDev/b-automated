# Gera dist\VisualAutomator: o programa, o Tesseract e os idiomas, sem precisar instalar nada no PC de destino.
# Uso: .\build_exe.ps1   (requer o venv com pyinstaller e o Tesseract instalado em C:\Program Files\Tesseract-OCR)

$ErrorActionPreference = "Stop"
$raiz = $PSScriptRoot
$py = Join-Path $raiz ".venv\Scripts\python.exe"
$tesseractOrigem = "C:\Program Files\Tesseract-OCR"

if (-not (Test-Path (Join-Path $tesseractOrigem "tesseract.exe"))) {
    throw "Tesseract nao encontrado em $tesseractOrigem"
}

& $py -m PyInstaller --noconfirm --clean --windowed --onedir --name VisualAutomator (Join-Path $raiz "app.py")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller falhou" }

$destino = Join-Path $raiz "dist\VisualAutomator"

# Idiomas do projeto (eng e por), usados pelo app via pasta_tessdata
Copy-Item (Join-Path $raiz "tessdata") $destino -Recurse -Force

# Tesseract: so o executavel, as DLLs e os idiomas basicos (sem as ferramentas de treinamento)
$tessDestino = Join-Path $destino "tesseract"
New-Item -ItemType Directory -Force -Path (Join-Path $tessDestino "tessdata") | Out-Null
Copy-Item (Join-Path $tesseractOrigem "tesseract.exe") $tessDestino -Force
Copy-Item (Join-Path $tesseractOrigem "*.dll") $tessDestino -Force
Copy-Item (Join-Path $tesseractOrigem "tessdata\eng.traineddata"), (Join-Path $tesseractOrigem "tessdata\osd.traineddata") (Join-Path $tessDestino "tessdata") -Force

Write-Host "Pronto: $destino\VisualAutomator.exe"
