# STATghost CudaText plugin — VP-EB-1 send-to-sniper (layer A).
# Transport = system clipboard UTF-8 (layer B). No REPL inside CudaText.
# Command class stays thin: new actions = method + install.inf.
# Native chrome (VP-EB-1b) = chrome.py — main toolbar + side tab.

from cudatext import APPSTATE_THEME_UI
from cudatext import app_proc, PROC_SET_CLIP
from cudatext import ed
from cudatext import msg_status

try:
    from . import chrome
    from . import config as plugincfg
    from . import editor
    from . import host
    from . import paths as sgpaths
    from . import prefs
    from . import protocol
    from .statement import (
        collapse_wraps,
        enclosing_function,
        extend_statement,
        join_lines,
    )
except ImportError:
    import chrome
    import config as plugincfg
    import editor
    import host
    import paths as sgpaths
    import prefs
    import protocol
    from statement import (
        collapse_wraps,
        enclosing_function,
        extend_statement,
        join_lines,
    )
PLUGIN = 'STATghost'


def _set_clip(text):
    app_proc(PROC_SET_CLIP, text)


def _line_count(text):
    if text is None or text == '':
        return 0
    t = text.replace('\r\n', '\n').replace('\r', '\n')
    return t.count('\n') + 1


def _r_quote(path):
    """R double-quoted path; prefer / separators (works on Win + Unix)."""
    s = (path or '').replace('\\', '/')
    return '"' + s.replace('"', '\\"') + '"'


def _send_code(text, mode, apply_collapse=True):
    """Student chunk — STATghost evals only when Armed.

    Collapse is plugin-side shaping of the EVAL body. STATghost then
    chooses 1 line → direct `>` echo vs 2+ → `source(echo=TRUE)` — so
    the option only “shows” when collapse actually yields one line.
    """
    if text is None or text.strip() == '':
        msg_status(PLUGIN + ': nothing to send (' + mode + ')')
        return False
    n_in = _line_count(text)
    collapse = prefs.get_collapse() if apply_collapse else False
    if collapse:
        text = collapse_wraps(text)
    n_out = _line_count(text)
    _set_clip(protocol.make_eval(text))
    msg_status(
        PLUGIN + ': sent ' + mode + ' (' + str(len(text))
        + ' chars, lines ' + str(n_in) + '→' + str(n_out)
        + ', collapse '
        + ('ON' if collapse else 'OFF')
        + ') — STATghost must be Armed'
    )
    return True


def _send_command(name, hint):
    """Control token — STATghost handles Idle or Armed; never evals it."""
    _set_clip(protocol.make_command(name))
    msg_status(PLUGIN + ': ' + hint)
    return True


def _statement_at_caret():
    """Prefer enclosing function (caret anywhere in body), else one statement."""
    y0 = editor.caret_line_index()
    if y0 is None:
        return None, None, '', 'statement'
    n = editor.line_count()
    fs, fe = enclosing_function(y0, editor.get_line, n)
    if fs is not None and fe is not None:
        text = join_lines(editor.get_line, fs, fe)
        return fs, fe, text, 'function'
    y = editor.skip_to_code_line(y0)
    if y is None:
        return None, None, '', 'statement'
    start, end = extend_statement(y, editor.get_line, n)
    text = join_lines(editor.get_line, start, end)
    return start, end, text, 'statement'


def _build_source_file_code():
    """source(.paths[4], …) only — buffer already written to the shared slot."""
    echo = 'TRUE' if prefs.get_source_echo() else 'FALSE'
    enc = prefs.encoding_for_r()
    return (
        'source(.paths[4], echo = ' + echo
        + ', spaced = FALSE, encoding = ' + _r_quote(enc) + ')'
    )


class Command:

    def send_selection(self):
        """Send selection; if empty, enclosing function or statement at caret.

        Function (RStudio-style): caret anywhere inside `f <- function() {…}`
        sends the whole definition, not only the inner line.
        """
        sel = editor.selection_text()
        if sel.strip() != '':
            last = editor.selection_last_line()
            if _send_code(sel, 'selection') and last is not None:
                editor.advance_caret_after(last)
            return
        _start, end, text, mode = _statement_at_caret()
        if _send_code(text, mode) and end is not None:
            editor.advance_caret_after(end)

    def send_file(self):
        """Whole buffer → TEMP/STATghost/file.R → source(.paths[4], …).

        TinnRcom pattern: shared `.paths` slot (STATghostcom), not an
        absolute editor path on the Console. Armed R + companion loaded.
        """
        text = ed.get_text_all()
        if text is None:
            text = ''
        try:
            sgpaths.write_slot(sgpaths.IDX_FILE, text)
        except OSError as e:
            msg_status(PLUGIN + ': cannot write .paths[4] — ' + str(e))
            return
        code = _build_source_file_code()
        _send_code(code, 'source-file', apply_collapse=False)

    def clear_console(self):
        """Ask STATghost to wipe Console text (Ctrl+L). Works Idle or Armed."""
        if not chrome.get(self).host_cmd_allowed():
            return
        _send_command(
            protocol.CMD_CLEAR,
            'clear Console requested — STATghost must be running',
        )

    def toggle_arm(self):
        """Ask STATghost to toggle Idle|Armed (works from Idle)."""
        _send_command(
            protocol.CMD_TOGGLE_ARM,
            'toggle Arm/Idle requested — STATghost must be running',
        )
        chrome.get(self).note_arm_toggle()
        chrome.get(self).refresh()

    def toggle_host(self):
        """Start STATghost if it is down; quit if it is up.

        Never from CudaText startup — only a conscious toolbar/menu click.
        """
        if not chrome.get(self).host_cmd_allowed():
            return
        if host.is_running():
            def _quit_clip():
                _set_clip(protocol.make_command(protocol.CMD_QUIT))

            ok, msg = host.stop_graceful(_quit_clip)
            if ok:
                msg_status(PLUGIN + ': ' + msg)
            chrome.get(self).note_host_down()
            chrome.get(self).refresh()
            return
        ok, msg = host.start()
        if ok:
            if msg == 'already running':
                msg_status(PLUGIN + ': already running — one instance')
            else:
                msg_status(PLUGIN + ': started ' + msg)
            chrome.get(self).note_host_up()
            chrome.get(self).refresh()
            return
        msg_status(PLUGIN + ': ' + msg)
        if plugincfg.show_config():
            ok, msg = host.start()
            if ok:
                if msg == 'already running':
                    msg_status(PLUGIN + ': already running — one instance')
                else:
                    msg_status(PLUGIN + ': started ' + msg)
                chrome.get(self).note_host_up()
            else:
                msg_status(PLUGIN + ': ' + msg)
        chrome.get(self).refresh()

    def config(self):
        """Plugin settings — STATghost executable path."""
        plugincfg.show_config()
        chrome.get(self).refresh()

    def open_side(self):
        """Sidebar button / Plugins → STATghost side tab."""
        chrome.get(self).open_side(activate=True, focus=True)

    def chrome_tick(self, tag='', info=''):
        chrome.get(self).tick(tag)

    def toggle_bar(self):
        """Retired experimental docked strip — point at native chrome."""
        msg_status(
            PLUGIN + ': docked bar retired — use the toolbar and the '
            'STATghost side tab'
        )

    def on_start2(self, ed_self):
        chrome.get(self).on_start()

    def on_state(self, ed_self, state):
        if state == APPSTATE_THEME_UI:
            chrome.get(self).reload_icons()
