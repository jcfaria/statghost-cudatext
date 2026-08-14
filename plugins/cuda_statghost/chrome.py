# Native CudaText chrome (VP-EB-1b).
# Toolbar + side *control deck* (mission §5): send and host commands
# stay in the editor so the classroom does not bounce to STATghost.
# Never embed Console / Plot / Explorer.

from __future__ import annotations

import os

from cudatext import ALIGN_CLIENT
from cudatext import ALIGN_TOP
from cudatext import BTN_GET_DATA2
from cudatext import BTN_SET_DATA1
from cudatext import BTN_SET_DATA2
from cudatext import BTN_SET_ENABLED
from cudatext import BTN_SET_HINT
from cudatext import BTN_SET_IMAGEINDEX
from cudatext import BTN_SET_IMAGELIST
from cudatext import BTN_SET_KIND
from cudatext import BTN_SET_TEXT
from cudatext import BTNKIND_ICON_ONLY
from cudatext import BTNKIND_SEP_HORZ
from cudatext import BTNKIND_TEXT_ICON_HORZ
from cudatext import DLG_CREATE
from cudatext import DLG_CTL_ADD
from cudatext import DLG_CTL_HANDLE
from cudatext import DLG_CTL_PROP_SET
from cudatext import DLG_PROP_SET
from cudatext import IMAGELIST_ADD
from cudatext import IMAGELIST_CREATE
from cudatext import IMAGELIST_GET_SIZE
from cudatext import IMAGELIST_SET_SIZE
from cudatext import LISTBOX_ADD
from cudatext import LISTBOX_DELETE_ALL
from cudatext import LISTBOX_SET_ITEM_H
from cudatext import LISTBOX_THEME
from cudatext import MENU_ENUM
from cudatext import MENU_REMOVE
from cudatext import PROC_GET_MAIN_TOOLBAR
from cudatext import PROC_SHOW_SIDEPANEL_SET
from cudatext import PROC_SIDEPANEL_ACTIVATE
from cudatext import PROC_SIDEPANEL_ADD_DIALOG
from cudatext import PROC_THEME_UI_DICT_GET
from cudatext import TIMER_START
from cudatext import TOOLBAR_ADD_ITEM
from cudatext import TOOLBAR_DELETE_BUTTON
from cudatext import TOOLBAR_GET_BUTTON_HANDLE
from cudatext import TOOLBAR_GET_COUNT
from cudatext import TOOLBAR_GET_IMAGELIST
from cudatext import TOOLBAR_SET_WRAP
from cudatext import TOOLBAR_THEME
from cudatext import TOOLBAR_UPDATE
from cudatext import app_proc
from cudatext import button_proc
from cudatext import dlg_proc
from cudatext import imagelist_proc
from cudatext import listbox_proc
from cudatext import menu_proc
from cudatext import msg_status
from cudatext import timer_proc
from cudatext import toolbar_proc

try:
    from . import host
    from . import icons as icontint
except ImportError:
    import host
    import icons as icontint

PLUGIN = 'STATghost'
TITLE = 'STATghost'
TAG = 'statghost-eb1'
TOOLS_CAP = 'Tools'
TICK_MS = 2000

# name, hint, Command method, icon file (or None = separator).
# Order: sep | SG chrome (Settings, Arm, Kill) | sep | editor Send/Clear.
# Same left-to-right as FormMain (Settings → Arm → Kill). Panel /
# Explorer / OnTop stay in STATghost. Clear Console is here (owner).
#
# GOLDEN RULE — side tab uses the exact same action order as the toolbar
# (separators skipped). Never invent a second sequence.
_TB = (
    ('sep', '-', None, None),
    ('cfg', 'STATghost plugin Config', 'config', 'setting-lines.png'),
    ('arm', 'Toggle Arm/Idle', 'toggle_arm', 'idle.png'),
    ('host', 'Start/Quit STATghost', 'toggle_host', 'power.png'),
    ('sep_send', '-', None, None),
    ('send', 'Send selection or statement', 'send_selection', 'send.png'),
    ('source', 'Source file via .paths[4]', 'send_file', 'export.png'),
    ('clear', 'Clear STATghost Console', 'clear_console', 'clear.png'),
)
_TB_NAMES = tuple(row[0] for row in _TB)

_SIDE_CAP = {
    'cfg': 'Config',
    'arm': 'Idle',
    'host': 'Start',
    'send': 'Send',
    'source': 'Source',
    'clear': 'Clear',
}
_SIDE = tuple(
    (name, _SIDE_CAP.get(name, name), method, icon)
    for name, _hint, method, icon in _TB
    if method is not None
)

_LEGACY_CAPS = (
    'Send to STATghost',
    'Send current line',
    'Toggle Arm/Idle',
    'Start/Quit STATghost',
    'Show/Hide sniper bar',
    'Config…',
    'Config...',
)


def _here():
    return os.path.dirname(os.path.realpath(__file__))


def _png_dir():
    return os.path.join(_here(), 'png')


def _icon_folder(px):
    if px >= 32:
        return '32px'
    if px >= 24:
        return '24px'
    return '16px'


def _cap_plain(item):
    cap = ''
    if isinstance(item, dict):
        cap = item.get('cap') or item.get('caption') or ''
    return cap.replace('&', '')


def _item_id(item):
    if isinstance(item, dict):
        return item.get('id') or item.get('Id')
    return None


def _item_tag(item):
    if isinstance(item, dict):
        return item.get('tag') or ''
    return ''


def _ui_color(name, fallback):
    d = app_proc(PROC_THEME_UI_DICT_GET, '') or {}
    item = d.get(name) or {}
    c = item.get('color')
    return c if isinstance(c, int) else fallback


def _rgb(r, g, b):
    return r | (g << 8) | (b << 16)


def _mid_ellipsis(text, n=36):
    if not text or len(text) <= n:
        return text
    keep = n - 1
    left = max(8, keep // 3)
    return text[:left] + '…' + text[-(keep - left):]


class Chrome:
    def __init__(self, cmd):
        self.cmd = cmd
        self._armed = False
        self._was_running = False
        self._btns = {}
        self._icons = {}
        self._imglist = None
        self._h_dlg = None
        self._h_side_list = None
        self._side_btns = {}
        self._side_icon_idx = {}
        self._side_ready = False
        self._timer = False
        # False while the toolbar is being built — ADD_ITEM must not
        # fire Start/Quit. STATghost never auto-starts with CudaText.
        self._host_cmd_ok = False

    def host_cmd_allowed(self):
        return bool(self._host_cmd_ok)

    def on_start(self):
        # Do not call host.start() here. Side tab opens only if SG
        # is already running (owner: no auto-launch with CudaText).
        remove_legacy_tools()
        self.install_toolbar()
        # [sidebar1] is an empty shell until ADD_DIALOG. Attach now so
        # a click (or a restored session) is not a blank panel.
        self._ensure_side()
        if host.is_running():
            self._was_running = True
            self._armed = False
            self.open_side(activate=True, focus=False)
        else:
            self.refresh()
        self._start_timer()
        self._host_cmd_ok = True

    def open_side(self, activate=True, focus=False):
        self._ensure_side()
        if activate:
            try:
                app_proc(PROC_SHOW_SIDEPANEL_SET, True)
            except Exception:
                pass
            app_proc(PROC_SIDEPANEL_ACTIVATE, (TITLE, bool(focus)))
        self.refresh()

    def note_arm_toggle(self):
        if host.is_running():
            self._armed = not self._armed

    def note_host_down(self):
        self._armed = False
        self._was_running = False

    def note_host_up(self):
        self._armed = False
        self._was_running = True

    def tick(self, tag=''):
        running = host.is_running()
        if running and not self._was_running:
            self._armed = False
        if (not running) and self._was_running:
            self._armed = False
        self._was_running = running
        self.refresh()

    def refresh(self):
        running = host.is_running()
        armed = bool(running and self._armed)
        if 'arm' in self._btns:
            button_proc(
                self._btns['arm'], BTN_SET_IMAGEINDEX,
                self._icons['armed' if armed else 'idle'],
            )
            button_proc(
                self._btns['arm'], BTN_SET_HINT,
                'Armed — click to Idle' if armed else 'Idle — click to Arm',
            )
        if 'host' in self._btns:
            button_proc(
                self._btns['host'], BTN_SET_IMAGEINDEX,
                self._icons['kill' if running else 'power'],
            )
            button_proc(
                self._btns['host'], BTN_SET_HINT,
                'Quit STATghost' if running else 'Start STATghost',
            )
        self._refresh_side(running, armed)

    def install_toolbar(self):
        try:
            h_bar = app_proc(PROC_GET_MAIN_TOOLBAR, '')
        except Exception:
            return
        if not h_bar:
            return
        self._load_icons(h_bar)
        if self._plugin_names(h_bar) != _TB_NAMES:
            self._drop_plugin_buttons(h_bar)
            self._create_toolbar(h_bar)
        else:
            self._btns = self._scan_toolbar(h_bar)
            self._restyle_seps(h_bar)
        self._apply_imglist()
        toolbar_proc(h_bar, TOOLBAR_UPDATE)

    def _create_toolbar(self, h_bar):
        self._btns = {}
        for name, hint, method, icon in _TB:
            h_btn = toolbar_proc(h_bar, TOOLBAR_ADD_ITEM)
            if h_btn is None:
                cnt = toolbar_proc(h_bar, TOOLBAR_GET_COUNT)
                h_btn = toolbar_proc(h_bar, TOOLBAR_GET_BUTTON_HANDLE, index=cnt - 1)
            if not h_btn:
                continue
            button_proc(h_btn, BTN_SET_DATA2, TAG + ':' + name)
            if icon is None:
                self._style_sep(h_btn)
                continue
            button_proc(h_btn, BTN_SET_KIND, BTNKIND_ICON_ONLY)
            button_proc(h_btn, BTN_SET_HINT, hint)
            idx = self._icons.get(icon, -1)
            button_proc(h_btn, BTN_SET_IMAGEINDEX, idx)
            button_proc(
                h_btn, BTN_SET_DATA1,
                'module=cuda_statghost;cmd=' + method + ';',
            )
            self._btns[name] = h_btn

    def _drop_plugin_buttons(self, h_bar):
        """Drop every plugin-tagged button (old order, leftover Line, seps)."""
        try:
            n = toolbar_proc(h_bar, TOOLBAR_GET_COUNT) or 0
        except Exception:
            return
        for i in range(n - 1, -1, -1):
            h_btn = toolbar_proc(h_bar, TOOLBAR_GET_BUTTON_HANDLE, index=i)
            if not h_btn:
                continue
            data2 = button_proc(h_btn, BTN_GET_DATA2) or ''
            if data2.startswith(TAG + ':'):
                toolbar_proc(h_bar, TOOLBAR_DELETE_BUTTON, index=i)

    def _style_sep(self, h_btn):
        # Same as TATFlatToolbar.AddSep on a horizontal bar: Kind=SepHorz
        # (thin vertical line). SepVert is the other orientation.
        button_proc(h_btn, BTN_SET_KIND, BTNKIND_SEP_HORZ)
        button_proc(h_btn, BTN_SET_ENABLED, False)

    def _restyle_seps(self, h_bar):
        try:
            n = toolbar_proc(h_bar, TOOLBAR_GET_COUNT) or 0
        except Exception:
            return
        for i in range(n):
            h_btn = toolbar_proc(h_bar, TOOLBAR_GET_BUTTON_HANDLE, index=i)
            if not h_btn:
                continue
            data2 = button_proc(h_btn, BTN_GET_DATA2) or ''
            if data2 in (TAG + ':sep', TAG + ':sep_send'):
                self._style_sep(h_btn)

    def _plugin_names(self, h_bar):
        names = []
        try:
            n = toolbar_proc(h_bar, TOOLBAR_GET_COUNT) or 0
        except Exception:
            return tuple()
        for i in range(n):
            h_btn = toolbar_proc(h_bar, TOOLBAR_GET_BUTTON_HANDLE, index=i)
            if not h_btn:
                continue
            data2 = button_proc(h_btn, BTN_GET_DATA2) or ''
            if data2.startswith(TAG + ':'):
                names.append(data2.split(':', 1)[1])
        return tuple(names)

    def _scan_toolbar(self, h_bar):
        found = {}
        try:
            n = toolbar_proc(h_bar, TOOLBAR_GET_COUNT) or 0
        except Exception:
            return found
        for i in range(n):
            h_btn = toolbar_proc(h_bar, TOOLBAR_GET_BUTTON_HANDLE, index=i)
            if not h_btn:
                continue
            data2 = button_proc(h_btn, BTN_GET_DATA2) or ''
            if not data2.startswith(TAG + ':'):
                continue
            name = data2.split(':', 1)[1]
            if not name.startswith('sep'):
                found[name] = h_btn
        return found

    def reload_icons(self):
        try:
            h_bar = app_proc(PROC_GET_MAIN_TOOLBAR, '')
        except Exception:
            h_bar = None
        self._load_icons(h_bar)
        self._apply_imglist()
        self.refresh()
        if h_bar:
            toolbar_proc(h_bar, TOOLBAR_UPDATE)

    def _apply_imglist(self):
        if not self._imglist:
            return
        keys = {
            'send': 'send.png',
            'source': 'export.png',
            'clear': 'clear.png',
            'arm': 'idle',
            'host': 'power',
            'cfg': 'setting-lines.png',
        }
        for name, h_btn in self._btns.items():
            button_proc(h_btn, BTN_SET_IMAGELIST, self._imglist)
            key = keys.get(name)
            if key:
                button_proc(h_btn, BTN_SET_IMAGEINDEX, self._icons.get(key, -1))

    def _load_icons(self, h_bar):
        px = 16
        if h_bar:
            host_list = toolbar_proc(h_bar, TOOLBAR_GET_IMAGELIST)
            if host_list:
                size = imagelist_proc(host_list, IMAGELIST_GET_SIZE)
                if isinstance(size, (tuple, list)) and size:
                    px = int(size[0])
        if self._imglist is None:
            self._imglist = imagelist_proc(0, IMAGELIST_CREATE, value=0)
        imagelist_proc(self._imglist, IMAGELIST_SET_SIZE, (px, px))
        folder = os.path.join(_png_dir(), _icon_folder(px))
        names = {
            'send.png': 'send.png',
            'export.png': 'export.png',  # Source file (provisional)
            'clear.png': 'clear.png',
            'armed': 'armed.png',
            'idle': 'idle.png',
            'power': 'power.png',
            'kill': 'kill.png',
            'setting-lines.png': 'setting-lines.png',
        }
        rgb = icontint.theme_rgb()
        for key, fname in names.items():
            path = os.path.join(folder, fname)
            idx = -1
            if os.path.isfile(path):
                load = path
                try:
                    load = icontint.tinted_path(path, rgb)
                except Exception:
                    load = path
                try:
                    idx = imagelist_proc(self._imglist, IMAGELIST_ADD, value=load)
                except Exception:
                    idx = -1
                if idx is None:
                    idx = -1
            self._icons[key] = idx
            self._icons[fname] = idx

    def _fill_imagelist(self, il, px):
        """Load the side-tab glyphs into *il*. Returns name → index."""
        out = {}
        if not il:
            return out
        imagelist_proc(il, IMAGELIST_SET_SIZE, (px, px))
        folder = os.path.join(_png_dir(), _icon_folder(px))
        files = {
            'send': 'send.png',
            'source': 'export.png',  # Source file (provisional)
            'clear': 'clear.png',
            'arm': 'idle.png',
            'armed': 'armed.png',
            'host': 'power.png',
            'kill': 'kill.png',
            'cfg': 'setting-lines.png',
        }
        rgb = icontint.theme_rgb()
        for key, fname in files.items():
            path = os.path.join(folder, fname)
            idx = -1
            if os.path.isfile(path):
                load = path
                try:
                    load = icontint.tinted_path(path, rgb)
                except Exception:
                    load = path
                try:
                    idx = imagelist_proc(il, IMAGELIST_ADD, value=load)
                except Exception:
                    idx = -1
                if idx is None:
                    idx = -1
            out[key] = idx
        return out

    def _ensure_side(self):
        if self._side_ready and self._h_dlg:
            return
        # gtk2: dlg_proc button_ex on_change is ignored until TFormDummy
        # DoShow sets IsFormShownAlready. A side-panel form is reparented
        # (not DLG_SHOW), so those clicks stay dead. Toolbar DATA1 is the
        # same path as the main CudaText bar, which already works here.
        h = dlg_proc(0, DLG_CREATE)
        if not h:
            print('STATghost side: DLG_CREATE failed')
            msg_status(PLUGIN + ': side tab — DLG_CREATE failed')
            return
        self._h_dlg = h
        dlg_proc(h, DLG_PROP_SET, prop={'cap': TITLE})
        n = dlg_proc(h, DLG_CTL_ADD, 'toolbar')
        dlg_proc(h, DLG_CTL_PROP_SET, index=n, prop={
            'name': 'bar',
            'align': ALIGN_TOP,
            'h': 28,
            'autosize': True,
        })
        h_bar = dlg_proc(h, DLG_CTL_HANDLE, index=n)
        self._side_btns = {}
        if h_bar:
            toolbar_proc(h_bar, TOOLBAR_THEME)
            il = toolbar_proc(h_bar, TOOLBAR_GET_IMAGELIST)
            side_icons = self._fill_imagelist(il, 16)
            for name, cap, method, _icon in _SIDE:
                toolbar_proc(h_bar, TOOLBAR_ADD_ITEM)
                cnt = toolbar_proc(h_bar, TOOLBAR_GET_COUNT) or 0
                hb = toolbar_proc(h_bar, TOOLBAR_GET_BUTTON_HANDLE, index=cnt - 1)
                if not hb:
                    continue
                button_proc(hb, BTN_SET_KIND, BTNKIND_TEXT_ICON_HORZ)
                button_proc(hb, BTN_SET_TEXT, cap)
                button_proc(hb, BTN_SET_HINT, cap)
                button_proc(hb, BTN_SET_IMAGEINDEX, side_icons.get(name, -1))
                button_proc(
                    hb, BTN_SET_DATA1,
                    'module=cuda_statghost;cmd=' + method + ';',
                )
                self._side_btns[name] = hb
            self._side_icon_idx = side_icons
            toolbar_proc(h_bar, TOOLBAR_SET_WRAP, index=True)
            toolbar_proc(h_bar, TOOLBAR_UPDATE)
        n = dlg_proc(h, DLG_CTL_ADD, 'listbox_ex')
        dlg_proc(h, DLG_CTL_PROP_SET, index=n, prop={
            'name': 'status',
            'align': ALIGN_CLIENT,
            'sp_l': 6,
            'sp_r': 6,
            'sp_t': 6,
            'sp_b': 6,
        })
        self._h_side_list = dlg_proc(h, DLG_CTL_HANDLE, index=n)
        if self._h_side_list:
            listbox_proc(self._h_side_list, LISTBOX_THEME)
            listbox_proc(self._h_side_list, LISTBOX_SET_ITEM_H, index=22)
        icon = os.path.join(_png_dir(), 'statghost_24.png')
        ok = app_proc(PROC_SIDEPANEL_ADD_DIALOG, (TITLE, h, icon))
        print('STATghost side: dlg=%s ADD_DIALOG=%s' % (h, ok))
        if not ok:
            msg_status(PLUGIN + ': side tab — ADD_DIALOG failed')
            return
        self._side_ready = True

    def _palette(self):
        font = _ui_color('ButtonFont', _rgb(0x90, 0x90, 0x90))
        back = _ui_color('EdTextBg', _ui_color('TabBg', _rgb(0x2A, 0x2A, 0x2A)))
        card = _ui_color('TabBg', _ui_color('ButtonBg', _rgb(0x38, 0x38, 0x38)))
        return {
            'font': font,
            'muted': _rgb(0x88, 0x88, 0x88),
            'back': back,
            'hdr': back,
            'card': card,
            'run': _rgb(0x4C, 0xAF, 0x50),
            'arm': _rgb(0xE6, 0xA8, 0x17),
            'stop': _rgb(0xC0, 0x5A, 0x5A),
        }

    def _refresh_side(self, running, armed):
        if 'arm' in self._side_btns:
            button_proc(
                self._side_btns['arm'], BTN_SET_TEXT,
                'Armed' if armed else 'Idle',
            )
            button_proc(
                self._side_btns['arm'], BTN_SET_IMAGEINDEX,
                self._side_icon_idx.get('armed' if armed else 'arm', -1),
            )
        if 'host' in self._side_btns:
            button_proc(
                self._side_btns['host'], BTN_SET_TEXT,
                'Quit' if running else 'Start',
            )
            button_proc(
                self._side_btns['host'], BTN_SET_IMAGEINDEX,
                self._side_icon_idx.get('kill' if running else 'host', -1),
            )
        if not self._h_side_list:
            return
        if running:
            lines = [
                'HOST    running',
                'ARM     Armed' if armed else 'ARM     Idle',
            ]
        else:
            lines = [
                'HOST    stopped',
                'ARM     —',
            ]
        lines.append(_mid_ellipsis(host.find_exe() or '(not found — Config)', 42))
        listbox_proc(self._h_side_list, LISTBOX_DELETE_ALL)
        for line in lines:
            listbox_proc(self._h_side_list, LISTBOX_ADD, text=line)

    def _start_timer(self):
        if self._timer:
            return
        timer_proc(
            TIMER_START,
            'module=cuda_statghost;cmd=chrome_tick;',
            TICK_MS,
        )
        self._timer = True


_chrome = None


def get(cmd=None):
    global _chrome
    if _chrome is None:
        _chrome = Chrome(cmd)
    elif cmd is not None:
        _chrome.cmd = cmd
    return _chrome


def remove_legacy_tools():
    """Drop the non-standard top-level Tools menu from the experimental bar."""
    try:
        items = menu_proc('top', MENU_ENUM) or []
    except Exception:
        return
    if not isinstance(items, list):
        return
    for it in items:
        if _cap_plain(it) != TOOLS_CAP:
            continue
        tid = _item_id(it)
        if not tid:
            continue
        ours = _item_tag(it) == TAG
        try:
            kids = menu_proc(tid, MENU_ENUM) or []
        except Exception:
            kids = []
        if isinstance(kids, list):
            for k in kids:
                ktag = _item_tag(k)
                kcap = _cap_plain(k)
                if ktag == TAG or kcap in _LEGACY_CAPS:
                    kid = _item_id(k)
                    if kid:
                        try:
                            menu_proc(kid, MENU_REMOVE)
                        except Exception:
                            pass
                    ours = True
        if ours:
            try:
                left = menu_proc(tid, MENU_ENUM) or []
            except Exception:
                left = []
            if not left:
                try:
                    menu_proc(tid, MENU_REMOVE)
                except Exception:
                    pass
        return
