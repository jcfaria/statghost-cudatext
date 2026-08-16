shared/ — universal STATghost plugin identity
=============================================
Updated: 2026-08-16
Repo: jcfaria/statghost-plugins  (was statghost-cudatext)

The student sees **STATghost** in every client: one Plugins menu, one
workbar (Send▾ / Source▾ / Inspect▾ / Clear▾), one clipboard contract.
The editor is only the host. Do not invent a second brand per IDE.

Contract (all hosts, all languages):
  1. Menu group **STATghost** (never "CudaText R" / "VS Code R").
  2. Workbar: same action ids / same relative order as
     `plugins/cudatext/cuda_statghost/chrome_show.py`
     (`ACTION_KEYS`, `NESTS`).
  3. Clipboard tokens `#. STATGHOST:<CMD> <nonce>` — twin of
     STATghost `src/ubridgecmd.pas` (`protocol.py` today).
  4. Send with no selection = enclosing function, else complete
     statement at caret, then advance. Engine = whatever STATghost
     has Armed (R / Python / Julia).
  5. D29: never embed Console / Plot / Explorer in the client.

Glyphs are the same identity on every host. Canonical stash:
  shared/png/          source drop (16/24/32 + brand)
The first host still ships a subset beside its CODE
(`plugins/cudatext/cuda_statghost/png/`) because CudaText loads
from the plugin package. Do not invent a second icon set per IDE.
explorer_filter / explorer_popup stay in the stash only (D29).

CODE that is host-agnostic (protocol, statement extract, rword,
chrome_show) still lives beside the first host
(`plugins/cudatext/cuda_statghost/`) until a second host has GO.
Then extract into this folder — do not copy-paste.

Host plugins live under `plugins/` (one parent, one subfolder each).
What is general stays at the repo root (`shared/`, lexers, docs).
What is specific to one host (CODE, install, TF, chrome SAP) lives
inside that host.

  plugins/cudatext/    first host — CODE (VP-EB-1 + workbar)
  plugins/vscode/      next candidate — RECORD (no CODE yet)
  plugins/notepadpp/   later — create only with GO
  …                    same identity, different host API

Tinn-R_D is a read-only peer, not a folder here.
