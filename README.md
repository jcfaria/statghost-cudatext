# STATghost-plugins

Public companion to **[STATghost](https://github.com/jcfaria/statghost)** —
peer plugins and canonical lexers. One identity for the student
(**STATghost** in the client: menu + unified workbar + clipboard contract).
Each editor is a host folder, not a separate product.

**Repo:** https://github.com/jcfaria/statghost-plugins  
Formerly `statghost-cudatext` (GitHub keeps a redirect).

STATghost remains the sniper matchbox. This repo owns **peer** artefacts —
not a REPL+Explorer bundle (D29).

## Layout

| Path | Role |
|------|------|
| `shared/` | Universal contract (menu, workbar, `#. STATGHOST:` protocol) |
| `cudatext/cuda_statghost/` | CudaText host plugin (VP-EB-1 + workbar) |
| `vscode/` | Next host (VS Code / Cursor) — folder reserved; no CODE yet |
| `lexer-dev/` | Workshop LCF packs |
| `lexer/` | Promoted packs (CudaText `data/lexlib` + STATghost Console via build) |
| `docs/` | Notes + optional sync into STATghost `_out/lexer` |
| `w_todo/` | WORKBAR SAP/CPR (VP-WB-*) |

The folder name on disk is the host; the menu caption is always
**STATghost**. Further hosts (`notepadpp/`, …) land only with GO.

## CudaText (Linux lab)

STATghost must be **running**. **Toggle Arm/Idle** works while Idle
(control token `#. STATGHOST:TOGGLE_ARM <nonce>` — never eval'd). Send
of code uses `#. STATGHOST:EVAL <nonce>` plus the student chunk, so the
same selection can be re-sent (pseudo-random reruns).
Eval still requires Armed. Empty selection → complete **statement** at the
caret (brackets, trailing operators, and unbraced R `if (cond)` plus
its multi-line body — RStudio Ctrl+Enter idea). After a successful
send, the caret advances to the next code line and **stops**.

```bash
bash cudatext/install_lab.sh
# or: CUDA_ROOT=/path/to/CudaText bash cudatext/install_lab.sh
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

TF: `bash cudatext/run_tf.sh` (unit + functional + production).
Workbar battery: `python3 cudatext/cuda_statghost/test_workbar.py`.

## Relationship

```
statghost-plugins/lexer   ← canonical packs
        │
        ├─→ CudaText data/lexlib
        └─→ STATghost src/build.ps1 → src/_out/lexer/

statghost-plugins/cudatext/cuda_statghost
        └─→ CudaText app/py/cuda_statghost  (symlink via cudatext/install_lab.sh)
```

STATghost source keeps **only** `lexer/README.txt` (no LCF duplicates;
no Pascal for EB-1 v1). Motto: Keep this project as simple and effective as possible.

---

## Author / Maintainer

Started and maintained by:

**Faria, J. C.**  
Universidade Estadual de Santa Cruz — UESC  
Departamento de Ciências Exatas — DCEX  
Ilhéus — Bahia — Brazil

---

## License

**Mozilla Public License 2.0 (MPL-2.0)** — see [`LICENSE`](LICENSE).
