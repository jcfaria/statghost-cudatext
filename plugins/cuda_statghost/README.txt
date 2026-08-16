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
  outline.py      document outline (sections + functions)
  ranges.py       send above/below / sniper chunk text helpers
  chrome.py       native toolbar + side tab (status + outline)
  bar.py          retired experimental docked strip (do not auto-show)
  test_unit.py    automated checks (no CudaText host)
  png/            toolbar / sidebar glyphs (16/24/32; no Explorer set)

TF (automatic, no human hands):
  bash plugins/run_tf.sh
  1) python3 test_unit.py              — headless
  2) python3 test_functional.py        — clipboard → running STATghost
  3) python3 test_production.py        — running CudaText plugin → STATghost
     R only (armed engine). Python extract is test_unit.py — a live
     def/for into R is a Console Error:. Reads keys.json
     (this lab: Ctrl+Space). Bootstraps /tmp/sg_prod_venv (python-xlib).
     Logs: /tmp/sg_tf/last.log

Send (no selection):
  1. If the caret is inside `name <- function(...) { … }` → whole function
     (innermost when nested). RStudio-style. Python: def/class + adjacent
     @decorators (innermost method; send dedents so the REPL accepts it).
  2. Else → complete statement at caret, then advance.
     Python: try/except/else/finally, if/elif/else, for/with, and """
     strings grow to a parseable unit when the caret is on the header
     (or except/else). Inner body lines stay one statement (dedented).

Also (Plugins → STATghost / hotkeys on first install):
  Ctrl+Enter     Send selection / function / statement
  Ctrl+Alt+B     Send above (start→caret)
  Ctrl+Alt+E     Send below (caret→EOF)
  Ctrl+Shift+S   Source file (.paths[4])
  Ctrl+Shift+O   Outline…
  Alt+-          Insert ` <- `
  Ctrl+Shift+M   Insert pipe (`|>` default; magrittr via prefs)
  Source selection / function → .paths[5]
  setwd to file directory
  Send sniper chunk (blank/# cut)
  Side tab: host status + outline (double-click to jump)

New classroom action:
  1. Command method in __init__.py (one-liner)
  2. install.inf [itemN]
  3. If it is a STATghost *command* (not student code): add the token
     in protocol.py AND src/ubridgecmd.pas (same spelling)
  4. If it should appear on the toolbar: add a row in chrome.py _TB

Config (Options → Settings-plugins → STATghost → Config):
  [host] exe=  — STATghost binary (empty = auto-detect)
  [send] collapse=1 (default): join editor wraps into one EVAL line
    (comma / `(` / `[`). `{` blocks keep newlines between statements.
    STATghost then echoes 1 line as `>` and 2+ as original wraps
    (`>` / `+`); `source(echo=TRUE)` is the Source-file button.
    Multi-line strings and unbraced `if` stay as-is.
  [send] source_echo=1 / source_encoding=utf-8 — Source file button
    writes the buffer to the shared TEMP/STATghost/file.R slot
    (STATghostcom `.paths[4]`, TinnRcom pattern), then sends only:
      source(.paths[4], echo = …, spaced = FALSE, encoding = …)
    Encoding is a combo_ro of CudaText PROC_ENUM_ENCODINGS (mapped to
    R names on send, e.g. utf-8 → UTF-8). R Armed + companion loaded.
    No absolute editor path on the Console.
  [edit] pipe=native|magrittr — Insert pipe (Ctrl+Shift+M): `|>` or `%>%`
  [icons] fg=auto|light|dark|theme — toolbar + side-tab glyph FG
    (default auto: high contrast vs ButtonBg/TabBg; theme = raw ButtonFont)
  [chrome] show=cfg,arm,host,send,function,above,below,chunk,source,srcsel,setwd,clear
    — which control-deck actions are ON (toolbar + side, same set /
    same relative order). Config checkboxes + All/None. Extra (opt-in):
    assign, pipe, outline. Empty → defaults (cores + Send/Source extras).
    Hidden actions remain in Plugins menu.

Chrome (VP-EB-1b + VP-WB-1, native):
  Default toolbar: Config | Arm/Idle | Start/Quit | Send▾ | Source▾ | Clear
  Send▾ nest: Function, Above, Below, Chunk (click still = Send).
  Source▾ nest: Src sel/fn, setwd (click still = Source file).
  GOLDEN RULE: same action ids / same relative order (_SIDE from _TB).
  Toolbar nests related extras; side tab stays expanded (captions).
  Visibility is one shared list (chrome.show) — never diverge bars.
  Opt-in: Insert <-, Insert pipe, Outline (flat; nest later).
  Send = selection, or the complete statement at caret.
  Function = enclosing function only.
  Source = whole saved file via `.path` + source(...).
  Arm/Idle and Start/Quit swap icons (on|off).
  Toolbar + side glyphs share one FG picker (icons.py / icons_fg.py);
  brand side-tab icon is left as-is. Reloads on theme / Config OK.
  Side tab "STATghost" (same row as Code tree / Projects):
    control deck — Host/Arm status + the same actions (mission §5).
    Not Console/Plot/Explorer. Opens on start only if STATghost is up.
  Plugins → STATghost for the same commands. No custom Tools menu.

Collapse vs STATghost (who does what):
  Plugin shapes the clipboard EVAL body (join wraps or not).
  STATghost EvalCode: 1 non-empty line → direct prompt echo;
  2+ lines → original wrap echo (`>`/`+`) then eval (not deparse).
  Both sides matter for what the student sees on the Console.

Atalhos: none by default — bind in CudaText Command Palette (F9).
Restart CudaText after Python changes.
