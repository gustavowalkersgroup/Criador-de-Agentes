# install.ps1 — instala as 4 skills NexTags no ~/.claude/skills/ no Windows.
# Uso: irm https://raw.githubusercontent.com/gustavowalkersgroup/Criador-de-Agentes/main/install.ps1 | iex
#      ou: .\install.ps1 (rodando localmente após clone)

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/gustavowalkersgroup/Criador-de-Agentes.git"
$Skills = @("nextags-prompt-creator", "nextags-prompt-fixer", "nextags-json-fixer", "nextags-mcp-builder")
$TargetDir = Join-Path $env:USERPROFILE ".claude\skills"

Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   NexTags Tools — Instalação de 4 Skills      ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# 1. Detecta ambiente local vs. via web
$NeedCleanup = $false
if ((Test-Path "./skills") -and (Test-Path "./.claude-plugin")) {
    Write-Host "✓ Detectado clone local. Usando skills locais." -ForegroundColor Green
    $SrcDir = "./skills"
} else {
    Write-Host "→ Modo remoto. Clonando repo temporariamente..." -ForegroundColor Yellow
    $TmpDir = New-Item -ItemType Directory -Path (Join-Path $env:TEMP "nextags-tools-$(Get-Random)") -Force
    & git clone --depth 1 $RepoUrl $TmpDir.FullName 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Falha ao clonar repo. Verifique se git está instalado e há acesso à internet." -ForegroundColor Red
        exit 1
    }
    $SrcDir = Join-Path $TmpDir.FullName "skills"
    $NeedCleanup = $true
}

# 2. Verifica Python
Write-Host "→ Verificando dependências..." -ForegroundColor Yellow
$PythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $PythonCmd = $cmd
        break
    }
}
if (-not $PythonCmd) {
    Write-Host "✗ Python não encontrado. As skills prompt-creator/prompt-fixer usam analyzer Python." -ForegroundColor Red
    Write-Host "   Instale Python 3.8+ e tente de novo." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python OK ($PythonCmd)" -ForegroundColor Green

# 3. Cria pasta destino
New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null

# 4. Copia cada skill
Write-Host ""
Write-Host "→ Instalando skills em $TargetDir..." -ForegroundColor Yellow
foreach ($skill in $Skills) {
    $skillSrc = Join-Path $SrcDir $skill
    $skillDst = Join-Path $TargetDir $skill

    if (-not (Test-Path $skillSrc)) {
        Write-Host "✗ Skill não encontrada no repo: $skill" -ForegroundColor Red
        continue
    }
    if (Test-Path $skillDst) {
        Write-Host "⚠  Já existe: $skill — fazendo backup .bak" -ForegroundColor Yellow
        $backup = "$skillDst.bak"
        if (Test-Path $backup) { Remove-Item $backup -Recurse -Force }
        Move-Item $skillDst $backup
    }
    Copy-Item $skillSrc $skillDst -Recurse -Force
    Write-Host "✓ Instalada: $skill" -ForegroundColor Green
}

# 5. Cleanup
if ($NeedCleanup -and (Test-Path $TmpDir)) {
    Remove-Item $TmpDir.FullName -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║         Instalação concluída! 🎉              ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Skills instaladas em: $TargetDir"
Write-Host ""
Write-Host "Como usar no Claude Code:"
Write-Host "  /nextags-prompt-creator   # gerar prompt do zero"
Write-Host "  /nextags-prompt-fixer     # auditar/corrigir prompt"
Write-Host "  /nextags-json-fixer       # validar saída JSON do agente"
Write-Host "  /nextags-mcp-builder      # construir MCP no n8n"
Write-Host ""
Write-Host "Backup das skills anteriores (se existirem): *.bak na mesma pasta."
