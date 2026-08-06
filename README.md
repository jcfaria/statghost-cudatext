# statghost-cudatext

Private companion to **[STATghost](https://github.com/jcfaria/statghost)** for the
**CudaText** ecosystem (lexers + future thin plugins).

STATghost remains the sniper matchbox. This repo owns **peer** CudaText
artefacts — not a REPL+Explorer bundle (D29).

## Layout

| Path | Role |
|------|------|
| `lexer-dev/` | Workshop LCF packs |
| `lexer/` | Promoted packs (CudaText `data/lexlib` + STATghost Console via build) |
| `plugins/` | Future VP-EB-1 / VP-EB-1b |
| `docs/` | Notes + optional sync into STATghost `_out/lexer` |

## Relationship

```
statghost-cudatext/lexer   ← canonical packs
        │
        ├─→ CudaText data/lexlib
        └─→ STATghost src/build.ps1 → src/_out/lexer/  (+ pack_choice.json)
```

STATghost source keeps **only** `lexer/README.txt` + `lexer/pack_choice.json`
(no LCF duplicates).

## Licence

MPL-2.0. Motto: Keep this project as simple and effective as possible.
