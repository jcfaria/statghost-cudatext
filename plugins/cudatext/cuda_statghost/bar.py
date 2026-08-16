# Retired (2026-08-13). Experimental docked strip — replaced by native
# chrome.py (main toolbar + side tab). Kept so leftover keybindings
# that imported this module do not crash. Do not auto-show.
# Does not embed Console / Plot / Explorer (docs/missao_objetivos.md §5).

from __future__ import annotations

from cudatext import DBORDER_NONE
from cudatext import DBORDER_TOOL
from cudatext import DLG_CREATE
from cudatext import DLG_CTL_ADD
from cudatext import DLG_CTL_PROP_SET
from cudatext import DLG_DOCK
from cudatext import DLG_HIDE
from cudatext import DLG_PROP_GET
from cudatext import DLG_PROP_SET
from cudatext import DLG_SHOW_NONMODAL
from cudatext import dlg_proc
from cudatext import ini_read
from cudatext import ini_write
from cudatext import msg_status
from cudatext import timer_proc
from cudatext import TIMER_START_ONE

try:
    from . import prefs
except ImportError:
    import prefs

PLUGIN = 'STATghost'
STRIP_H = 36
BTN_H = 28
PAD = 4

# name, caption, hint, width, Command method (or None = hide bar)
_BUTTONS = (
    ('send', 'Send', 'Send selection or complete statement', 64, 'send_selection'),
    ('arm', 'Arm/Idle', 'Toggle STATghost Arm/Idle', 88, 'toggle_arm'),
    ('host', 'Start/Quit', 'Start STATghost if down; quit if up', 96, 'toggle_host'),
    ('hide', 'Hide', 'Hide this bar (Tools -> Show/Hide sniper bar)', 56, None),
)


def _ini_path():
    return prefs.ini_path()


class SniperBar:

    def __init__(self, command):
        self.cmd = command
        self.h = None
        self._btn_index = {}
        self._docked = False

    def restore_on_start(self):
        # Retired: never auto-show. Native chrome is chrome.py.
        return

    def _deferred_show(self, tag=''):
        self.show(quiet=True)

    def toggle(self):
        if self._is_visible():
            self.hide()
        else:
            self.show()

    def _is_visible(self):
        if not self.h:
            return False
        p = dlg_proc(self.h, DLG_PROP_GET) or {}
        return bool(p.get('vis'))

    def hide(self):
        if self.h:
            dlg_proc(self.h, DLG_HIDE)
        ini_write(_ini_path(), 'bar', 'vis', '0')
        msg_status(PLUGIN + ': sniper bar hidden')

    def show(self, quiet=False):
        if not self.h:
            self._build()
        elif self._docked:
            dlg_proc(self.h, DLG_DOCK, prop='T', index=0)
        dlg_proc(self.h, DLG_SHOW_NONMODAL)
        ini_write(_ini_path(), 'bar', 'vis', '1')
        if not quiet:
            msg_status(PLUGIN + ': sniper bar shown')

    def _build(self):
        h = dlg_proc(0, DLG_CREATE)
        self.h = h
        total_w = PAD
        for _n, _c, _hint, w, _m in _BUTTONS:
            total_w += w + PAD
        dlg_proc(h, DLG_PROP_SET, prop={
            'cap': PLUGIN,
            'w': total_w,
            'h': STRIP_H,
            'h_min': STRIP_H,
            'h_max': STRIP_H,
            'border': DBORDER_NONE,
            'taskbar': 2,
            'topmost': False,
            'on_close_query': self._on_close_query,
        })
        x = PAD
        self._btn_index = {}
        for name, cap, hint, w, method in _BUTTONS:
            idc = dlg_proc(h, DLG_CTL_ADD, 'button')
            dlg_proc(h, DLG_CTL_PROP_SET, index=idc, prop={
                'name': name,
                'cap': cap,
                'hint': hint,
                'x': x,
                'y': PAD,
                'w': w,
                'h': BTN_H,
                'on_change': self._on_btn,
            })
            self._btn_index[idc] = method
            x += w + PAD
        try:
            dlg_proc(h, DLG_DOCK, prop='T', index=0)
            self._docked = True
        except Exception:
            dlg_proc(h, DLG_PROP_SET, prop={'border': DBORDER_TOOL})
            self._docked = False

    def _on_close_query(self, id_dlg, id_ctl, data='', info=''):
        self.hide()
        return False

    def _on_btn(self, id_dlg, id_ctl, data='', info=''):
        method = self._btn_index.get(id_ctl)
        if method is None:
            self.hide()
            return
        fn = getattr(self.cmd, method, None)
        if fn:
            fn()
