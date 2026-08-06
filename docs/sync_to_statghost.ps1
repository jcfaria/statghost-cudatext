# Sync promoted lexer/ into STATghost build output (beside EXE).
# Prefer: powershell -File src/build.ps1 in the STATghost repo.
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

New-Item -ItemType Directory -Path (Split-Path $OutLexer -Parent) -Force | Out-Null
if (Test-Path -LiteralPath $OutLexer) { Remove-Item -LiteralPath $OutLexer -Recurse -Force }
Copy-Item -LiteralPath $CompanionLexer -Destination $OutLexer -Recurse -Force
Write-Host "OK $CompanionLexer -> $OutLexer"
