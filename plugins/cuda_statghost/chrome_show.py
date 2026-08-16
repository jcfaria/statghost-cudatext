# Shared toolbar / side-tab visibility (pure — no CudaText).
# One show-list for both bars (same action ids / same relative order).
# Toolbar may nest related extras under a parent (Tinn TBRMain analogue);
# the side tab stays expanded (vertical captions).

from __future__ import annotations

# Canonical action ids — order matches chrome._TB (minus separators).
ACTION_KEYS = (
    'cfg', 'arm', 'host',
    'send', 'function', 'above', 'below', 'chunk',
    'source', 'srcsel', 'setwd', 'clear',
    'assign', 'pipe', 'outline',
)
# Classroom default: six cores + Send/Source extras (compacted on the
# main toolbar via NESTS; still listed on the side tab).
DEFAULT_SHOW = (
    'cfg', 'arm', 'host',
    'send', 'function', 'above', 'below', 'chunk',
    'source', 'srcsel', 'setwd',
    'clear',
)

# Parent → related extras. Click = parent action; arrow = children.
# First approach only — Tinn Explorer / Packages / Knitr stay OUT.
NESTS = (
    ('send', ('function', 'above', 'below', 'chunk')),
    ('source', ('srcsel', 'setwd')),
)

_GROUP_HOST = frozenset(('cfg', 'arm', 'host'))
_GROUP_SEND = frozenset((
    'send', 'function', 'above', 'below', 'chunk',
    'source', 'srcsel', 'setwd', 'clear',
))
_GROUP_EDIT = frozenset(('assign', 'pipe', 'outline'))
_GROUPS = (_GROUP_HOST, _GROUP_SEND, _GROUP_EDIT)


def parse_show(raw, default=None):
    """Parse CSV / whitespace list → ordered tuple of known action keys."""
    if default is None:
        default = DEFAULT_SHOW
    if raw is None:
        return tuple(default)
    text = str(raw).strip()
    if text == '':
        return tuple(default)
    parts = []
    for chunk in text.replace(';', ',').replace(' ', ',').split(','):
        key = chunk.strip().lower()
        if key in ACTION_KEYS and key not in parts:
            parts.append(key)
    if not parts:
        return tuple(default)
    return tuple(k for k in ACTION_KEYS if k in parts)


def format_show(keys):
    """CSV for ini — only known keys, canonical order."""
    return ','.join(parse_show(','.join(keys or ()), default=()))


def nest_children(parent):
    """Related extras for a parent button (empty if none)."""
    for name, kids in NESTS:
        if name == parent:
            return kids
    return ()


def nest_menu_keys(parent, show_keys):
    """Children of *parent* that are currently shown (menu contents)."""
    if show_keys is None:
        show = set(DEFAULT_SHOW)
    else:
        keys = tuple(show_keys)
        if not keys:
            return ()
        show = set(parse_show(','.join(keys), default=()))
    return tuple(k for k in nest_children(parent) if k in show)


def collapse_nested_rows(tb_rows):
    """Drop child buttons whose parent is already on the bar.

    Separators with no remaining neighbours are left for the caller;
    filter_toolbar_rows already places seps between groups.
    """
    present = {row[0] for row in tb_rows if row[2] is not None}
    hide = set()
    for parent, kids in NESTS:
        if parent in present:
            hide.update(k for k in kids if k in present)
    if not hide:
        return tuple(tb_rows)
    return tuple(row for row in tb_rows if row[0] not in hide)


def filter_toolbar_rows(tb_rows, show_keys):
    """Filter _TB-like rows: leading sep + visibles + mid seps between groups.

    tb_rows: iterable of (name, hint, method, icon); method is None for seps.
    show_keys: iterable of action ids. Explicit empty → no buttons.
    Does **not** collapse nests — call collapse_nested_rows for the
    main toolbar. Side tab uses the uncollapsed list.
    """
    if show_keys is None:
        show = set(DEFAULT_SHOW)
    else:
        keys = tuple(show_keys)
        if not keys:
            return ()
        show = set(parse_show(','.join(keys), default=()))
        if not show:
            return ()
    actions = [
        row for row in tb_rows
        if row[2] is not None and row[0] in show
    ]
    if not actions:
        return ()
    buckets = []
    for group in _GROUPS:
        part = [r for r in actions if r[0] in group]
        if part:
            buckets.append(part)
    out = []
    if tb_rows and tb_rows[0][2] is None:
        out.append(tb_rows[0])
    seps = [row for row in tb_rows if row[2] is None]
    mid_seps = seps[1:] if len(seps) > 1 else []
    for i, part in enumerate(buckets):
        if i > 0:
            if i - 1 < len(mid_seps):
                out.append(mid_seps[i - 1])
            else:
                out.append(('sep_%d' % i, '-', None, None))
        out.extend(part)
    return tuple(out)


def filter_side_actions(side_rows, show_keys):
    """Filter side (name, cap, method, icon) rows — no separators, no nest hide."""
    if show_keys is None:
        show = set(DEFAULT_SHOW)
    else:
        keys = tuple(show_keys)
        if not keys:
            return ()
        show = set(parse_show(','.join(keys), default=()))
    return tuple(row for row in side_rows if row[0] in show)
