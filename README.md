# statghost-cudatext

Private companion to **[STATghost](https://github.com/jcfaria/statghost)** for the
**CudaText** ecosystem (lexers + thin peer plugins).

STATghost remains the sniper matchbox. This repo owns **peer** CudaText
artefacts — not a REPL+Explorer bundle (D29).

## Layout

| Path | Role |
|------|------|
| `lexer-dev/` | Workshop LCF packs |
| `lexer/` | Promoted packs (CudaText `data/lexlib` + STATghost Console via build) |
| `plugins/cuda_statghost/` | **VP-EB-1** send-to-sniper + Arm toggle (`protocol.py` / `editor.py` / `statement.py`) |
| `docs/` | Notes + optional sync into STATghost `_out/lexer` |

## VP-EB-1 plugin (Linux lab)

STATghost must be **running**. **Toggle Arm/Idle** works while Idle
(control token `#. STATGHOST:TOGGLE_ARM <nonce>` — never eval'd). Send
of code uses `#. STATGHOST:EVAL <nonce>` plus the student chunk, so the
same selection can be re-sent (pseudo-random reruns).
still requires Armed. Empty selection → complete **statement** at the
caret (brackets, trailing operators, and unbraced R `if (cond)` plus
its multi-line body — RStudio Ctrl+Enter idea). After a successful
send, the caret advances to the next code line and **stops**.

```bash
bash plugins/install_lab.sh
# or: CUDA_ROOT=/path/to/CudaText bash plugins/install_lab.sh
```

Restart CudaText (`cuda_jcf/run.sh`) after plugin changes (Python is
cached until restart). Then:

- **Plugins → STATghost → Send selection or statement**
- **Plugins → STATghost → Toggle Arm/Idle**
- **Plugins → STATghost → Start/Quit STATghost**
- Shortcuts: none by default — bind in Command Palette → **F9**

Engine = whatever STATghost has Armed (R / Python / Julia). Same chunk
sent twice without a clipboard change is skipped (same as a human Copy).

Do **not** embed a REPL inside CudaText.

## Relationship

```
statghost-cudatext/lexer   ← canonical packs
        │
        ├─→ CudaText data/lexlib
        └─→ STATghost src/build.ps1 → src/_out/lexer/

statghost-cudatext/plugins/cuda_statghost
        └─→ CudaText app/py/cuda_statghost  (symlink via install_lab.sh)
```

STATghost source keeps **only** `lexer/README.txt` (no LCF duplicates;
no Pascal for EB-1 v1).

## Licence

MPL-2.0. Motto: Keep this project as simple and effective as possible.
