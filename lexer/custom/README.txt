lexer/custom/ — lab custom Cuda lexers
=======================================================
Updated: 2026-08-05

Contents
--------
- Text file.lcf (+ map) — lab text / .txt highlighter

R
-
Product R lives in parent `lexer/` (STATghost slim from `lexer-dev/R/`).
The old custom lab `R.lcf` was removed (2026-08-05).

Stock Python|Julia live in parent `lexer/` (loaded by InitLibrary).
These custom copies are kept for packaging / future Settings import; they
are not auto-merged into InitLibrary (same LexerName would collide).
