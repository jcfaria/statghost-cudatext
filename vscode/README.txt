vscode/ — next STATghost host (VS Code / Cursor)
================================================
Updated: 2026-08-16
Status: **RECORD** — folder reserved; no extension CODE yet.
Repo: jcfaria/statghost-plugins

The student menu caption is **STATghost** (never "VS Code R" /
"R Editor"). Same identity as `cudatext/`: menu + workbar +
`#. STATGHOST:<CMD>` clipboard contract. See `../shared/README.txt`.

This folder is the next candidate after the CudaText host.
Cursor uses the VS Code extension API — one extension covers both
when CODE lands. Do not open a second brand or a second repo.

When there is GO (VP-EB-* for this host):
  1. Keep the contract in `shared/` (extract host-agnostic Python
     from `cudatext/cuda_statghost/` then; do not copy-paste).
  2. This folder becomes the VS Code / Cursor adapter only
     (package.json, activation, commands, toolbar).
  3. D29 still holds: no Console / Plot / Explorer inside the IDE.

Until GO: this README only. No empty `package.json`, no marketplace
stub, no keymap invent.
