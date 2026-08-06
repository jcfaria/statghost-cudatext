lexer/ — promoted CudaText / STATghost Console packs
=======================================================
Updated: 2026-08-06
Repo: jcfaria/statghost-cudatext (canonical)

Edit source: `../lexer-dev/`. After validate in CudaText, copy packs here,
then sync into:
  - CudaText `data/lexlib`
  - STATghost `lexer/` (Console beside EXE; excludes `pack_choice.json`)

Contents
--------
- `R.lcf` + `R.cuda-lexmap` — STATghost slim R
- `Python.lcf` + `Python.cuda-lexmap`
- `Julia.lcf` + `Julia.cuda-lexmap`
- `Text file.lcf` + `Text file.cuda-lexmap`
- `custom/` — lab copies not auto-loaded (LexerName collision)

`pack_choice.json` is **not** stored here (STATghost Settings only).
