# Plugin config UI (VP-EB-1). Path to the STATghost binary — classroom machines
# do not have the sibling-clone layout. D45: [OK] [Cancel], Cancel is default.
# dlg_custom (not dlg_proc): gtk2 TButton on_change via bound methods never
# fired — checkbox worked, OK/Cancel painted dead. Opened from Options →
# Settings-plugins → STATghost → Config.

from __future__ import annotations

import os

from cudatext import PROC_ENUM_ENCODINGS
from cudatext import app_proc
from cudatext import dlg_custom
from cudatext import dlg_file
from cudatext import msg_status

try:
    from . import chrome_show
    from . import host
    from . import prefs
except ImportError:
    import chrome_show
    import host
    import prefs

PLUGIN = 'STATghost'
_C1 = chr(1)

# Spacious classroom Config (owner: was too cramped).
_W = 480
_H = 560

# Indices must match the control list below (top → bottom).
_IDX_COLLAPSE = 0
_IDX_SRC_ECHO = 1
_IDX_ENC_LBL = 2
_IDX_ENC = 3
_IDX_PIPE_LBL = 4
_IDX_PIPE = 5
_IDX_ICONS_LBL = 6
_IDX_ICONS = 7
_IDX_SHOW_LBL = 8
_IDX_ALL = 9
_IDX_NONE = 10
# 15 chrome checks (11..25)
_IDX_CHK0 = 11
_SHOW_DEFS = (
    ('cfg', 'Config'),
    ('arm', 'Arm/Idle'),
    ('host', 'Start/Quit'),
    ('send', 'Send'),
    ('function', 'Function'),
    ('above', 'Above'),
    ('below', 'Below'),
    ('chunk', 'Chunk'),
    ('source', 'Source'),
    ('srcsel', 'Src sel/fn'),
    ('clear', 'Clear'),
    ('setwd', 'setwd'),
    ('assign', 'Insert <-'),
    ('pipe', 'Insert pipe'),
    ('outline', 'Outline'),
)
_IDX_EXE_LBL = _IDX_CHK0 + len(_SHOW_DEFS)
_IDX_EXE = _IDX_EXE_LBL + 1
_IDX_BROWSE = _IDX_EXE + 1
_IDX_HINT = _IDX_BROWSE + 1
_IDX_DET = _IDX_HINT + 1
_IDX_OK = _IDX_DET + 1
_IDX_CANCEL = _IDX_OK + 1

_PIPE_ITEMS = ('|>  (native R 4.1+)', '%>%  (magrittr)')
_ICONS_FG_ITEMS = (
    'auto  (contrast vs theme)',
    'light  (light icons)',
    'dark  (dark icons)',
    'theme  (ButtonFont raw)',
)
_ICONS_FG_KEYS = ('auto', 'light', 'dark', 'theme')

_FALLBACK_ENCS = (
    'utf-8',
    'utf-16 le',
    'utf-16 be',
    'cp1252',
    'iso-8859-1',
    'latin1',
    'cp850',
    'koi8-r',
)


def _ctl(*parts):
    return _C1.join(parts)


def _as_bool(val):
    if val is True or val == 1:
        return True
    if val is False or val == 0:
        return False
    s = str(val if val is not None else '').strip().lower()
    return s in ('1', 'true', 'yes', 'on')


def _short_path(text, n=48):
    if not text or len(text) <= n:
        return text
    keep = n - 1
    left = max(10, keep // 3)
    return text[:left] + '…' + text[-(keep - left):]


def _cuda_encodings():
    try:
        raw = app_proc(PROC_ENUM_ENCODINGS, '')
    except Exception:
        raw = None
    out = []
    if isinstance(raw, (list, tuple)):
        out = [str(x).strip() for x in raw if str(x).strip()]
    elif isinstance(raw, str) and raw.strip():
        parts = raw.replace('\r', '\n').replace('\t', '\n').split('\n')
        out = [p.strip() for p in parts if p.strip()]
    if not out:
        out = list(_FALLBACK_ENCS)
    low = [e.lower() for e in out]
    for pref in ('utf-8', 'utf8', 'UTF-8'):
        if pref.lower() in low:
            i = low.index(pref.lower())
            if i > 0:
                out.insert(0, out.pop(i))
                low = [e.lower() for e in out]
            break
    return out


def _enc_index(encs, wanted):
    w = (wanted or '').strip().lower().replace('_', '-')
    if not w:
        w = 'utf-8'
    aliases = {
        'utf8': 'utf-8',
        'utf-8 bom': 'utf-8',
        'utf8 bom': 'utf-8',
        'utf-8': 'utf-8',
        'latin-1': 'iso-8859-1',
        'latin1': 'iso-8859-1',
    }
    w = aliases.get(w, w)
    for i, e in enumerate(encs):
        el = e.lower().replace('_', '-')
        if el == w or aliases.get(el, el) == w:
            return i
    for i, e in enumerate(encs):
        if e.lower().startswith('utf-8') or e.lower() == 'utf8':
            return i
    return 0


def _pipe_index():
    tok = prefs.get_pipe_token()
    return 1 if tok == '%>%' else 0


def _icons_fg_index():
    key = prefs.get_icons_fg()
    try:
        return _ICONS_FG_KEYS.index(key)
    except ValueError:
        return 0


def _show_dict_from_prefs():
    on = set(prefs.get_chrome_show())
    return {key: (key in on) for key, _cap in _SHOW_DEFS}


def _read_show_from_res(res, show_on):
    out = dict(show_on)
    for i, (key, _cap) in enumerate(_SHOW_DEFS):
        idx = _IDX_CHK0 + i
        if idx in res:
            out[key] = _as_bool(res.get(idx))
    return out


def _check_grid_ctls(show_on):
    """3-column checkbox grid with comfortable row pitch."""
    rows = []
    cols = (
        (12, 150),
        (168, 310),
        (328, 468),
    )
    y0 = 214
    row_h = 30
    for i, (key, cap) in enumerate(_SHOW_DEFS):
        r = i // 3
        c = i % 3
        x1, x2 = cols[c]
        y1 = y0 + r * row_h
        y2 = y1 + 26
        rows.append(_ctl(
            'type=check',
            'cap=' + cap,
            'val=' + ('1' if show_on.get(key) else '0'),
            'pos=%d,%d,%d,%d' % (x1, y1, x2, y2),
        ))
    return rows


def show_config():
    path = prefs.get_exe() or host.find_exe(ignore_ini=True) or ''
    collapse = prefs.get_collapse()
    src_echo = prefs.get_source_echo()
    encoding = prefs.get_source_encoding()
    encs = _cuda_encodings()
    enc_idx = _enc_index(encs, encoding)
    pipe_idx = _pipe_index()
    icons_idx = _icons_fg_index()
    show_on = _show_dict_from_prefs()
    detected = host.find_exe(ignore_ini=True) or ''
    det_cap = (
        ('Detected: ' + _short_path(detected)) if detected else ''
    )

    # Checkbox block ends ~ y=214+5*30=364; exe below with air.
    y_exe_lbl = 378
    y_exe = 400
    y_hint = 436
    y_det = 458
    y_ok = 520

    while True:
        ctls = [
            _ctl('type=check',
                 'cap=Send wraps as one Console line',
                 'val=' + ('1' if collapse else '0'),
                 'pos=12,10,468,36'),
            _ctl('type=check',
                 'cap=Source file: echo = TRUE',
                 'val=' + ('1' if src_echo else '0'),
                 'pos=12,42,468,68'),
            _ctl('type=label', 'cap=Source file encoding',
                 'pos=12,82,220,104'),
            _ctl('type=combo_ro',
                 'items=' + '\t'.join(encs),
                 'val=' + str(enc_idx),
                 'pos=230,78,468,108'),
            _ctl('type=label', 'cap=Insert pipe (Ctrl+Shift+M)',
                 'pos=12,120,220,142'),
            _ctl('type=combo_ro',
                 'items=' + '\t'.join(_PIPE_ITEMS),
                 'val=' + str(pipe_idx),
                 'pos=230,116,468,146'),
            _ctl('type=label', 'cap=Toolbar / side icons FG',
                 'pos=12,158,220,180'),
            _ctl('type=combo_ro',
                 'items=' + '\t'.join(_ICONS_FG_ITEMS),
                 'val=' + str(icons_idx),
                 'pos=230,154,468,184'),
            _ctl('type=label',
                 'cap=Toolbar / side buttons (same set)',
                 'pos=12,196,300,214'),
            _ctl('type=button', 'cap=All',
                 'pos=320,192,388,218'),
            _ctl('type=button', 'cap=None',
                 'pos=396,192,468,218'),
        ]
        ctls.extend(_check_grid_ctls(show_on))
        ctls.extend([
            _ctl('type=label', 'cap=STATghost executable',
                 'pos=12,%d,300,%d' % (y_exe_lbl, y_exe_lbl + 20)),
            _ctl('type=edit', 'name=exe', 'val=' + path,
                 'pos=12,%d,360,%d' % (y_exe, y_exe + 28)),
            _ctl('type=button', 'cap=Browse…',
                 'pos=372,%d,468,%d' % (y_exe, y_exe + 28)),
            _ctl('type=label',
                 'cap=Empty = auto-detect. Hidden buttons stay in Plugins menu.',
                 'pos=12,%d,468,%d' % (y_hint, y_hint + 18)),
            _ctl('type=label', 'cap=' + det_cap,
                 'pos=12,%d,468,%d' % (y_det, y_det + 18)),
            _ctl('type=button', 'cap=OK',
                 'pos=268,%d,362,%d' % (y_ok, y_ok + 28)),
            _ctl('type=button', 'cap=Cancel', 'ex0=1',
                 'pos=374,%d,468,%d' % (y_ok, y_ok + 28)),
        ])
        text = '\n'.join(ctls)
        res = dlg_custom(PLUGIN + ' plugin', _W, _H, text, get_dict=True)
        if res is None:
            return False
        path = (res.get(_IDX_EXE) or '').strip()
        try:
            enc_idx = int(str(res.get(_IDX_ENC) if res.get(_IDX_ENC) is not None else enc_idx))
        except (TypeError, ValueError):
            enc_idx = _enc_index(encs, encoding)
        if enc_idx < 0 or enc_idx >= len(encs):
            enc_idx = _enc_index(encs, 'utf-8')
        encoding = encs[enc_idx]
        try:
            pipe_idx = int(str(res.get(_IDX_PIPE) if res.get(_IDX_PIPE) is not None else pipe_idx))
        except (TypeError, ValueError):
            pipe_idx = _pipe_index()
        if pipe_idx not in (0, 1):
            pipe_idx = 0
        try:
            icons_idx = int(str(
                res.get(_IDX_ICONS) if res.get(_IDX_ICONS) is not None else icons_idx
            ))
        except (TypeError, ValueError):
            icons_idx = _icons_fg_index()
        if icons_idx < 0 or icons_idx >= len(_ICONS_FG_KEYS):
            icons_idx = 0
        collapse = _as_bool(res.get(_IDX_COLLAPSE))
        src_echo = _as_bool(res.get(_IDX_SRC_ECHO))
        show_on = _read_show_from_res(res, show_on)
        clicked = res.get('clicked')
        if clicked == _IDX_ALL:
            show_on = {key: True for key, _c in _SHOW_DEFS}
            continue
        if clicked == _IDX_NONE:
            show_on = {key: False for key, _c in _SHOW_DEFS}
            continue
        if clicked == _IDX_BROWSE:
            init_dir = os.path.dirname(path) if path else ''
            init_name = os.path.basename(path) if path else host.exe_name()
            filt = 'STATghost|' + host.exe_name() + '|All|*'
            picked = dlg_file(
                True, init_name, init_dir, filt, 'STATghost executable',
            )
            if picked:
                path = picked
            continue
        if clicked != _IDX_OK:
            return False
        if path and (not os.path.isfile(path)):
            msg_status(PLUGIN + ': file not found — ' + path)
            continue
        chosen = [key for key, _c in _SHOW_DEFS if show_on.get(key)]
        if not chosen:
            chosen = list(chrome_show.DEFAULT_SHOW)
            msg_status(PLUGIN + ': no buttons selected — restored defaults')
        prefs.set_exe(path)
        prefs.set_collapse(collapse)
        prefs.set_source_echo(src_echo)
        prefs.set_source_encoding(encoding)
        prefs.set_pipe_token('magrittr' if pipe_idx == 1 else 'native')
        prefs.set_icons_fg(_ICONS_FG_KEYS[icons_idx])
        prefs.set_chrome_show(chosen)
        msg_status(
            PLUGIN + ': settings saved — buttons '
            + ','.join(prefs.get_chrome_show())
            + ', icons FG '
            + prefs.get_icons_fg()
        )
        return True
