cuda_statghost — thin CudaText peer plugin (VP-EB-1 + EB-1b chrome)
==================================================================

STATghost stays the receiver. This plugin never embeds a REPL,
Plot, or Explorer (docs/missao_objetivos.md §5).

Layout (add a module, not a god-file):

  install.inf     CudaText commands + [sidebar1]
  __init__.py     Command only
  protocol.py     clipboard contract (`#. STATGHOST:<CMD> <nonce>`)
  host.py         find / start the STATghost process (quit = QUIT token)
  prefs.py        cuda_statghost.ini (exe path + send / source prefs)
  paths.py        TEMP/STATghost slots twin of STATghostcom `.paths`
  config.py       plugin Config UI
  editor.py       caret / selection / advance
  statement.py    R statement bounds + enclosing function + collapse_wraps
  chrome.py       native toolbar + side tab (cuda_r_plugin API recipe)
  bar.py          retired experimental docked strip (do not auto-show)
  test_unit.py    automated checks (no CudaText): collapse / protocol / paths / function
  png/            toolbar / sidebar glyphs (16/24/32; no Explorer set)

TF (no host):
  python3 test_unit.py

Send (no selection):
  1. If the caret is inside `name <- function(...) { … }` (any body line,
     brace, or blank/comment in the block) → send the **whole function**
     (innermost when nested). Same idea as RStudio “run function”.
  2. Else → complete statement at caret (brackets / if-else), then advance.

New classroom action:
  1. Command method in __init__.py (one-liner)
  2. install.inf [itemN]
  3. If it is a STATghost *command* (not student code): add the token
     in protocol.py AND src/ubridgecmd.pas (same spelling)
  4. If it should appear on the toolbar: add a row in chrome.py _TB

Config (Options → Settings-plugins → STATghost → Config):
  [host] exe=  — STATghost binary (empty = auto-detect)
  [send] collapse=1 (default): join editor wraps into one EVAL line
    (comma / `(` / unmatched brackets). STATghost then uses the
    1-line `>` path instead of multi-line `source(echo=TRUE)`.
    Multi-line strings and unbraced `if` stay as-is.
  [send] source_echo=1 / source_encoding=utf-8 — Source file button
    writes the buffer to the shared TEMP/STATghost/file.R slot
    (STATghostcom `.paths[4]`, TinnRcom pattern), then sends only:
      source(.paths[4], echo = …, spaced = FALSE, encoding = …)
    Encoding is a combo_ro of CudaText PROC_ENUM_ENCODINGS (mapped to
    R names on send, e.g. utf-8 → UTF-8). R Armed + companion loaded.
    No absolute editor path on the Console.

Chrome (VP-EB-1b, native):
  Main toolbar: Config | Arm/Idle | Start/Quit | Send | Source | Clear
  GOLDEN RULE: side-tab order == toolbar order (_SIDE from _TB).
  Send = selection, or the complete statement at caret.
  Source = whole saved file via `.path` + source(...).
  Arm/Idle and Start/Quit swap icons (on|off).
  Toolbar glyphs are tinted to the UI theme ButtonFont (icons.py);
  brand side-tab icon is left as-is.
  Side tab "STATghost" (same row as Code tree / Projects):
    control deck — Host/Arm status + the same actions (mission §5).
    Not Console/Plot/Explorer. Opens on start only if STATghost is up.
  Plugins → STATghost for the same commands. No custom Tools menu.

Collapse vs STATghost (who does what):
  Plugin shapes the clipboard EVAL body (join wraps or not).
  STATghost EvalCode: 1 non-empty line → direct prompt echo;
  2+ lines → source(echo=TRUE, spaced=FALSE). Both sides matter for
  what the student sees on the Console.

Atalhos: none by default — bind in CudaText Command Palette (F9).
Restart CudaText after Python changes.
