# install.ps1 — instala as 5 skills NexTags no ~/.claude/skills/ no Windows.
# Uso: irm https://raw.githubusercontent.com/gustavowalkersgroup/Criador-de-Agentes/main/install.ps1 | iex
#      ou: .\install.ps1 (rodando localmente após clone)

# IMPORTANTE: NÃO usar $ErrorActionPreference = "Stop" — git/native commands escrevem
# mensagens informativas em stderr (ex: "Cloning into..."), o que dispara exception
# fatal com Stop. Usamos checagem manual de $LASTEXITCODE.
$ErrorActionPreference = "Continue"

$RepoUrl = "https://github.com/gustavowalkersgroup/Criador-de-Agentes.git"
$Skills = @("nextags-prompt-creator", "nextags-prompt-fixer", "nextags-json-fixer", "nextags-mcp-builder", "nextags-webchat-tester")
$TargetDir = Join-Path $env:USERPROFILE ".claude\skills"

function Write-Status {
    param([string]$Symbol, [string]$Message, [string]$Color = "White")
    Write-Host "$Symbol " -NoNewline -ForegroundColor $Color
    Write-Host $Message
}

Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   NexTags Tools — Instalação de 5 Skills      ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# 1. Detecta ambiente local vs. via web
$NeedCleanup = $false
$TmpDir = $null

if ((Test-Path "./skills") -and (Test-Path "./.claude-plugin")) {
    Write-Status "✓" "Detectado clone local. Usando skills locais." "Green"
    $SrcDir = (Resolve-Path "./skills").Path
} else {
    Write-Status "→" "Modo remoto. Clonando repo temporariamente..." "Yellow"

    # Verifica se git está disponível
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Status "✗" "Git não encontrado. Instale Git for Windows: https://git-scm.com/download/win" "Red"
        exit 1
    }

    $TmpDirPath = Join-Path $env:TEMP "nextags-tools-$(Get-Random)"

    # Descarta stderr (mensagens "Cloning into..." vão pra stderr mesmo em sucesso)
    # e checa apenas o exit code do git
    & git clone --depth 1 $RepoUrl $TmpDirPath 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Status "✗" "Falha ao clonar repo (exit code $LASTEXITCODE). Verifique acesso à internet e se o repo está público." "Red"
        Write-Host "   URL: $RepoUrl"
        exit 1
    }

    if (-not (Test-Path (Join-Path $TmpDirPath "skills"))) {
        Write-Status "✗" "Clone feito mas pasta 'skills/' não encontrada no repo." "Red"
        exit 1
    }

    $TmpDir = $TmpDirPath
    $SrcDir = Join-Path $TmpDir "skills"
    $NeedCleanup = $true
    Write-Status "✓" "Repo clonado em $TmpDir" "Green"
}

# 2. Verifica Python
Write-Status "→" "Verificando dependências..." "Yellow"
$PythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $PythonCmd = $cmd
        break
    }
}
if (-not $PythonCmd) {
    Write-Status "⚠" "Python não encontrado. Skills prompt-creator/prompt-fixer usam analyzer Python." "Yellow"
    Write-Host "   Recomendado: instalar Python 3.8+ depois (https://python.org)."
    Write-Host "   A instalação continua, mas os analyzers não vão rodar até Python estar disponível."
} else {
    Write-Status "✓" "Python OK ($PythonCmd)" "Green"
}

# 3. Cria pasta destino
if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    Write-Status "✓" "Pasta criada: $TargetDir" "Green"
}

# 4. Copia cada skill
Write-Host ""
Write-Status "→" "Instalando skills em $TargetDir..." "Yellow"
$InstalledCount = 0
$FailedCount = 0
foreach ($skill in $Skills) {
    $skillSrc = Join-Path $SrcDir $skill
    $skillDst = Join-Path $TargetDir $skill

    if (-not (Test-Path $skillSrc)) {
        Write-Status "✗" "Skill não encontrada no repo: $skill" "Red"
        $FailedCount++
        continue
    }

    if (Test-Path $skillDst) {
        # Move backups pra FORA de ~/.claude/skills/ pra não aparecerem no Claude Code
        $backupDir = Join-Path $env:USERPROFILE ".claude\skills-backup"
        if (-not (Test-Path $backupDir)) {
            New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        }
        $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $backup = Join-Path $backupDir "$skill-$timestamp"
        Write-Status "⚠" " Já existe: $skill — backup em ~/.claude/skills-backup/" "Yellow"
        Move-Item $skillDst $backup -Force -ErrorAction SilentlyContinue
    }

    try {
        Copy-Item $skillSrc $skillDst -Recurse -Force
        Write-Status "✓" "Instalada: $skill" "Green"
        $InstalledCount++
    } catch {
        Write-Status "✗" "Falha ao copiar $skill : $_" "Red"
        $FailedCount++
    }
}

# 5. Cleanup
if ($NeedCleanup -and $TmpDir -and (Test-Path $TmpDir)) {
    Remove-Item $TmpDir -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ""
if ($FailedCount -eq 0) {
    Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║         Instalação concluída! 🎉              ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Green
} else {
    Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Yellow
    Write-Host "║  Instalação parcial — $InstalledCount OK, $FailedCount falharam   ║" -ForegroundColor Yellow
    Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Skills instaladas em: $TargetDir"
Write-Host ""
Write-Host "Como usar no Claude Code:"
Write-Host "  /nextags-prompt-creator   # gerar prompt do zero"
Write-Host "  /nextags-prompt-fixer     # auditar/corrigir prompt"
Write-Host "  /nextags-json-fixer       # validar saída JSON do agente"
Write-Host "  /nextags-mcp-builder      # construir MCP no n8n"
Write-Host "  /nextags-webchat-tester   # testar o agente publicado no webchat"
Write-Host ""
Write-Host "Backup das skills anteriores (se existirem): *.bak na mesma pasta."

if (-not $PythonCmd) {
    Write-Host ""
    Write-Host "⚠ Lembrete: instale Python pra usar os analyzers." -ForegroundColor Yellow
}
