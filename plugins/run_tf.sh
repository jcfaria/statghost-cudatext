#!/usr/bin/env bash
# Automatic TF for cuda_statghost — no human hands.
# 1) unit (headless)  2) functional (clipboard→SG)  3) production (CudaText→SG)
set -euo pipefail
DIR="$(cd "$(dirname "$0")/cuda_statghost" && pwd)"
LOGDIR="${SG_TF_LOGDIR:-/tmp/sg_tf}"
mkdir -p "$LOGDIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG="$LOGDIR/tf_$STAMP.log"
exec > >(tee -a "$LOG") 2>&1

PY="${SG_PROD_PY:-/tmp/sg_prod_venv/bin/python}"
if [[ ! -x "$PY" ]] || ! "$PY" -c 'from Xlib.ext import xtest' 2>/dev/null; then
  echo "==> bootstrap /tmp/sg_prod_venv (python-xlib)"
  python3 -m venv /tmp/sg_prod_venv
  /tmp/sg_prod_venv/bin/pip -q install python-xlib
  PY=/tmp/sg_prod_venv/bin/python
fi

echo "==> unit  $(date -Iseconds)"
python3 "$DIR/test_unit.py" -q
echo "==> functional (clipboard → STATghost)"
python3 "$DIR/test_functional.py" -q
echo "==> production (CudaText plugin → STATghost)"
"$PY" "$DIR/test_production.py" -q
echo "RESULT=BOK  log=$LOG"
ln -sfn "$LOG" "$LOGDIR/last.log"
