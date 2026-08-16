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
     `cudatext/cuda_statghost/chrome_show.py` (`ACTION_KEYS`, `NESTS`).
  3. Clipboard tokens `#. STATGHOST:<CMD> <nonce>` — twin of
     STATghost `src/ubridgecmd.pas` (`protocol.py` today).
  4. Send with no selection = enclosing function, else complete
     statement at caret, then advance. Engine = whatever STATghost
     has Armed (R / Python / Julia).
  5. D29: never embed Console / Plot / Explorer in the client.

CODE that is host-agnostic (protocol, statement extract, rword,
chrome_show, glyphs) still lives beside the first host
(`cudatext/cuda_statghost/`) until a second host has GO. Then extract
into this folder — do not copy-paste.

Host folders:
  cudatext/    first host — CODE (VP-EB-1 + workbar)
  vscode/      next candidate — RECORD (VS Code / Cursor; no CODE yet)
  notepadpp/   later — create only with GO
  …            same identity, different host API

Tinn-R_D is a read-only peer, not a folder here.
