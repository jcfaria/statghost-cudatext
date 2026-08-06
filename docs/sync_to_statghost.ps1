# Sync promoted lexer/ into a STATghost *build output* (beside EXE), not into
# the product source tree. Prefer: powershell -File src/build.ps1
# Manual (lab):
#   powershell -File docs/sync_to_statghost.ps1
#   powershell -File docs/sync_to_statghost.ps1 -OutLexer 'D:\...\statghost\src\_out\lexer'

param(
  [string]$OutLexer = ''
)

$ErrorActionPreference = 'Stop'
$CompanionRoot = Split-Path $PSScriptRoot -Parent
$CompanionLexer = Join-Path $CompanionRoot 'lexer'
$GitHub = Split-Path $CompanionRoot -Parent
if ($OutLexer -eq '') {
  $OutLexer = Join-Path $GitHub 'statghost\src\_out\lexer'
}

if (-not (Test-Path -LiteralPath $CompanionLexer)) {
  throw "Companion lexer/ not found: $CompanionLexer"
}

$PackChoice = Join-Path $GitHub 'statghost\lexer\pack_choice.json'
New-Item -ItemType Directory -Path (Split-Path $OutLexer -Parent) -Force | Out-Null
if (Test-Path -LiteralPath $OutLexer) { Remove-Item -LiteralPath $OutLexer -Recurse -Force }
Copy-Item -LiteralPath $CompanionLexer -Destination $OutLexer -Recurse -Force
if (Test-Path -LiteralPath $PackChoice) {
  Copy-Item -LiteralPath $PackChoice -Destination (Join-Path $OutLexer 'pack_choice.json') -Force
}
Write-Host "OK $CompanionLexer -> $OutLexer"
