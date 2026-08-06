# Sync promoted lexer/ packs into a local STATghost clone (Console ship tree).
# Default sibling path: ..\statghost\lexer
# Usage (from this repo root):
#   powershell -File docs/sync_to_statghost.ps1
#   powershell -File docs/sync_to_statghost.ps1 -StatghostRoot 'D:\path\to\statghost'

param(
  [string]$StatghostRoot = (Join-Path (Split-Path $PSScriptRoot -Parent | Split-Path -Parent) 'statghost')
)

$ErrorActionPreference = 'Stop'
$CompanionLexer = Join-Path (Split-Path $PSScriptRoot -Parent) 'lexer'
$Dest = Join-Path $StatghostRoot 'lexer'

if (-not (Test-Path -LiteralPath $CompanionLexer)) {
  throw "Companion lexer/ not found: $CompanionLexer"
}
if (-not (Test-Path -LiteralPath $StatghostRoot)) {
  throw "STATghost root not found: $StatghostRoot"
}

New-Item -ItemType Directory -Path $Dest -Force | Out-Null
# Preserve STATghost Settings file if present
$PackChoice = Join-Path $Dest 'pack_choice.json'
$PackBak = $null
if (Test-Path -LiteralPath $PackChoice) {
  $PackBak = Join-Path $env:TEMP ("statghost_pack_choice_{0}.json" -f [guid]::NewGuid().ToString('N'))
  Copy-Item -LiteralPath $PackChoice -Destination $PackBak -Force
}

robocopy $CompanionLexer $Dest /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
$code = $LASTEXITCODE
if ($code -ge 8) { throw "robocopy failed with exit $code" }

if ($PackBak) {
  Copy-Item -LiteralPath $PackBak -Destination $PackChoice -Force
  Remove-Item -LiteralPath $PackBak -Force
}

Write-Host "OK synced $CompanionLexer -> $Dest (pack_choice.json preserved if it existed)"
