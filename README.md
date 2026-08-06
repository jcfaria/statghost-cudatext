# statghost-cudatext

Private companion to **[STATghost](https://github.com/jcfaria/statghost)** for the
**CudaText** ecosystem (lexers + future thin plugins).

STATghost remains the sniper matchbox (clipboard → R|Python|Julia → text/plot).
This repo owns **peer** CudaText artefacts — not a REPL+Explorer bundle inside
CudaText (product decision D29 / packs 16–17).

## Layout

| Path | Role |
|------|------|
| `lexer-dev/` | Workshop LCF packs (edit here, validate in CudaText) |
| `lexlib/` | Promoted packs ready to copy into CudaText `data/lexlib` |
| `plugins/` | Future VP-EB-1 / VP-EB-1b plugins (send-to-sniper, TOC, Tools-like) |
| `docs/` | Sync notes; contract pointers back to STATghost `w_todo` |

## Relationship

```
CudaText (editor workspace)
    ↑ plugins/ + lexlib/     ← this repo
STATghost (sniper HWNDs: Console|Plot|Explorer)
    ↑ lexer/ beside EXE      ← still vendored in jcfaria/statghost for shipping
```

- **Geometry / Explorer dock** = STATghost only (`window_geometry.json`, VP-EX-1b).
- **Send selection → STATghost** = future plugin here (VP-EB-1).
- Related lab (bridge CSB): `jcfaria/cudatext-statghost-bridge` (keep until
  EB-1 absorbs or supersedes it).

## Promote lexers

1. Edit under `lexer-dev/<Lang>/`.
2. Copy `*.lcf` + `*.cuda-lexmap` → `lexlib/`.
3. Install into CudaText `data/lexlib` (lab: GitHub CudaText app and/or
   portable Dropbox `&_port/cudatext`).
4. Sync the same files into STATghost `lexer/` when shipping the Console HG
   (script or manual — keep packs identical).

## Licence

MPL-2.0 (same as STATghost). Co-authors on Python/Julia LCF notes:
Alexey Torgashin (CudaText) + José Cláudio Faria (STATghost / Tinn-R).

## Motto

Keep this project as simple and effective as possible.
