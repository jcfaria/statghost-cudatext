#!/usr/bin/env bash
# Lab install: symlink this plugin into the portable CudaText that
# cuda_jcf/run.sh launches (app/py beside the binary).
# Default: sibling ../CudaText  (Documents/Github/CudaText).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_SRC="$HERE/cuda_statghost"
CUDA_ROOT="${CUDA_ROOT:-}"
if [[ -z "$CUDA_ROOT" ]]; then
  CUDA_ROOT="$(cd "$HERE/../../CudaText" 2>/dev/null && pwd || true)"
fi

if [[ -z "${CUDA_ROOT}" || ! -d "$CUDA_ROOT/app/py" ]]; then
  echo "ERRO: CudaText app/py nao encontrado." >&2
  echo "Passe CUDA_ROOT=/caminho/para/CudaText (pasta que contem app/)." >&2
  exit 1
fi

TARGET="$CUDA_ROOT/app/py/cuda_statghost"
if [[ -e "$TARGET" || -L "$TARGET" ]]; then
  rm -rf "$TARGET"
fi
ln -sfn "$PLUGIN_SRC" "$TARGET"
echo "Plugin: $TARGET -> $PLUGIN_SRC"

echo
echo "Reinicie o CudaText (./cuda_jcf/run.sh)."
echo "Menu: Plugins -> STATghost  e  Tools -> Send / Toggle Arm"
echo "Atalhos: Command Palette (F9) — o utilizador define as teclas."
echo "STATghost tem de estar a correr. Toggle Arm funciona em Idle."
