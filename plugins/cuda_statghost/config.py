# Plugin config UI (VP-EB-1). Path to the STATghost binary — classroom machines
# do not have the sibling-clone layout. D45: [OK] [Cancel], Cancel is default.
# dlg_custom (not dlg_proc): gtk2 TButton on_change via bound methods never
# fired — checkbox worked, OK/Cancel painted dead. Opened from Options →
# Settings-plugins → STATghost → Config.
# Size: compact (~CudaText comment-config scale), not a full Settings page.

from __future__ import annotations

import os

from cudatext import PROC_ENUM_ENCODINGS
from cudatext import app_proc
from cudatext import dlg_custom
from cudatext import dlg_file
from cudatext import msg_status

try:
    from . import host
    from . import prefs
except ImportError:
    import host
    import prefs

PLUGIN = 'STATghost'
_C1 = chr(1)

# Client size — collapse + Source echo/encoding + pipe + exe.
_W = 420
_H = 276

# Indices must match the control list below (top → bottom).
_IDX_COLLAPSE = 0
_IDX_SRC_ECHO = 1
_IDX_ENC_LBL = 2
_IDX_ENC = 3
_IDX_PIPE_LBL = 4
_IDX_PIPE = 5
_IDX_EXE_LBL = 6
_IDX_EXE = 7
_IDX_BROWSE = 8
_IDX_HINT = 9
_IDX_DET = 10
_IDX_OK = 11
_IDX_CANCEL = 12

_PIPE_ITEMS = ('|>  (native R 4.1+)', '%>%  (magrittr)')

# Fallback if PROC_ENUM_ENCODINGS is empty (very old CudaText).
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
    """dlg_custom check val is normally '0'/'1'; tolerate odd gtk2 returns."""
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
    """CudaText encoding names (PROC_ENUM_ENCODINGS)."""
    try:
        raw = app_proc(PROC_ENUM_ENCODINGS, '')
    except Exception:
        raw = None
    out = []
    if isinstance(raw, (list, tuple)):
        out = [str(x).strip() for x in raw if str(x).strip()]
    elif isinstance(raw, str) and raw.strip():
        # Some builds return a single string; split defensively.
        parts = raw.replace('\r', '\n').replace('\t', '\n').split('\n')
        out = [p.strip() for p in parts if p.strip()]
    if not out:
        out = list(_FALLBACK_ENCS)
    # Prefer utf-8 near the top for classroom default.
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
    """Index of wanted encoding in encs (case-insensitive); else utf-8/0."""
    w = (wanted or '').strip().lower().replace('_', '-')
    if not w:
        w = 'utf-8'
    # Normalize common aliases for matching.
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


def show_config():
    path = prefs.get_exe() or host.find_exe(ignore_ini=True) or ''
    collapse = prefs.get_collapse()
    src_echo = prefs.get_source_echo()
    encoding = prefs.get_source_encoding()
    encs = _cuda_encodings()
    enc_idx = _enc_index(encs, encoding)
    pipe_idx = _pipe_index()
    detected = host.find_exe(ignore_ini=True) or ''
    det_cap = (
        ('Detected: ' + _short_path(detected)) if detected else ''
    )

    while True:
        text = '\n'.join([
            _ctl('type=check',
                 'cap=Send wraps as one Console line',
                 'val=' + ('1' if collapse else '0'),
                 'pos=8,6,404,28'),
            _ctl('type=check',
                 'cap=Source file: echo = TRUE',
                 'val=' + ('1' if src_echo else '0'),
                 'pos=8,32,404,54'),
            _ctl('type=label', 'cap=Source file encoding',
                 'pos=8,60,200,76'),
            _ctl('type=combo_ro',
                 'items=' + '\t'.join(encs),
                 'val=' + str(enc_idx),
                 'pos=210,58,404,82'),
            _ctl('type=label', 'cap=Insert pipe (Ctrl+Shift+M)',
                 'pos=8,88,220,104'),
            _ctl('type=combo_ro',
                 'items=' + '\t'.join(_PIPE_ITEMS),
                 'val=' + str(pipe_idx),
                 'pos=230,86,404,110'),
            _ctl('type=label', 'cap=STATghost executable',
                 'pos=8,118,280,134'),
            _ctl('type=edit', 'name=exe', 'val=' + path,
                 'pos=8,136,300,160'),
            _ctl('type=button', 'cap=Browse…',
                 'pos=308,136,404,160'),
            _ctl('type=label',
                 'cap=Empty = auto-detect (sibling / PATH).',
                 'pos=8,166,404,182'),
            _ctl('type=label', 'cap=' + det_cap,
                 'pos=8,182,404,198'),
            _ctl('type=button', 'cap=OK',
                 'pos=220,236,308,260'),
            _ctl('type=button', 'cap=Cancel', 'ex0=1',
                 'pos=316,236,404,260'),
        ])
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
        collapse = _as_bool(res.get(_IDX_COLLAPSE))
        src_echo = _as_bool(res.get(_IDX_SRC_ECHO))
        clicked = res.get('clicked')
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
        prefs.set_exe(path)
        prefs.set_collapse(collapse)
        prefs.set_source_echo(src_echo)
        prefs.set_source_encoding(encoding)
        prefs.set_pipe_token('magrittr' if pipe_idx == 1 else 'native')
        got = prefs.get_collapse()
        msg_status(
            PLUGIN + ': settings saved — collapse '
            + ('ON' if got else 'OFF')
            + ', source echo '
            + ('TRUE' if prefs.get_source_echo() else 'FALSE')
            + ', pipe '
            + prefs.get_pipe_token()
            + ', encoding '
            + prefs.get_source_encoding()
        )
        return True
