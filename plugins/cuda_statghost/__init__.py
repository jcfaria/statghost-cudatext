# STATghost CudaText plugin — VP-EB-1 send-to-sniper (layer A).
# Transport = system clipboard UTF-8; Armed STATghost evaluates (layer B).
# Engine-agnostic: whatever sniper engine is Armed. No REPL inside CudaText.

from cudatext import ed
from cudatext import app_proc, PROC_SET_CLIP
from cudatext import msg_status
from cudatext import menu_proc, MENU_ENUM, MENU_ADD

PLUGIN = 'STATghost'
TOOLS_CAP = 'Tools'
TOOLS_TAG = 'statghost-eb1'


def _caret_line_index():
    carets = ed.get_carets()
    if not carets:
        return None
    _x, y, _x2, _y2 = carets[0]
    if y < 0:
        return None
    return y


def _selection_text():
    sel = ed.get_text_sel()
    if sel:
        return sel
    return ''


def _current_line_text():
    y = _caret_line_index()
    if y is None:
        return ''
    line = ed.get_text_line(y)
    return line if line else ''


def _send_payload(text, mode):
    """Copy UTF-8 text to the system clipboard (same as a human Copy)."""
    if text is None or text.strip() == '':
        msg_status(PLUGIN + ': nothing to send (' + mode + ')')
        return
    app_proc(PROC_SET_CLIP, text)
    n = len(text)
    msg_status(
        PLUGIN + ': sent ' + mode + ' (' + str(n)
        + ' chars) — STATghost must be Armed'
    )


def _cap_plain(item):
    cap = ''
    if isinstance(item, dict):
        cap = item.get('cap') or item.get('caption') or ''
    return cap.replace('&', '')


def _item_id(item):
    if isinstance(item, dict):
        return item.get('id') or item.get('Id')
    return None


class Command:

    def __init__(self):
        self._tools_ready = False

    def send_selection(self):
        """Send selection; if empty, send the current line (CPR VP-EB-1)."""
        sel = _selection_text()
        if sel.strip() != '':
            _send_payload(sel, 'selection')
            return
        _send_payload(_current_line_text(), 'line')

    def send_current_line(self):
        _send_payload(_current_line_text(), 'line')

    def on_start2(self, ed_self):
        self._ensure_tools_menu()

    def _ensure_tools_menu(self):
        if self._tools_ready:
            return
        try:
            items = menu_proc('top', MENU_ENUM) or []
        except Exception:
            return
        if not isinstance(items, list):
            return

        tools_id = None
        plugins_index = -1
        for i, it in enumerate(items):
            cap = _cap_plain(it)
            if cap == TOOLS_CAP:
                tools_id = _item_id(it)
            elif cap == 'Plugins':
                plugins_index = i

        if tools_id is None:
            insert_at = plugins_index + 1 if plugins_index >= 0 else -1
            tools_id = menu_proc(
                'top', MENU_ADD,
                caption='&' + TOOLS_CAP,
                index=insert_at,
                tag=TOOLS_TAG,
            )

        if not tools_id:
            return

        existing = []
        try:
            kids = menu_proc(tools_id, MENU_ENUM) or []
        except Exception:
            kids = []
        if isinstance(kids, list):
            existing = [_cap_plain(k) for k in kids]

        pairs = (
            ('Send to STATghost', self.send_selection),
            ('Send current line', self.send_current_line),
        )
        for cap, fn in pairs:
            if cap in existing:
                continue
            menu_proc(
                tools_id, MENU_ADD,
                command=fn,
                caption=cap,
                tag=TOOLS_TAG,
            )
        self._tools_ready = True
