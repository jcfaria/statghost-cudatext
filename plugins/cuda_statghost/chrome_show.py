# Shared toolbar / side-tab visibility (pure — no CudaText).
# One show-list for both bars (golden rule: same actions, same order).

from __future__ import annotations

# Canonical action ids — order matches chrome._TB (minus separators).
ACTION_KEYS = (
    'cfg', 'arm', 'host',
    'send', 'function', 'above', 'below', 'chunk', 'source', 'srcsel', 'clear',
    'setwd', 'assign', 'pipe', 'outline',
)
# Classroom default: original control deck only (extras opt-in via Config).
DEFAULT_SHOW = ('cfg', 'arm', 'host', 'send', 'source', 'clear')

_GROUP_HOST = frozenset(('cfg', 'arm', 'host'))
_GROUP_SEND = frozenset((
    'send', 'function', 'above', 'below', 'chunk', 'source', 'srcsel', 'clear',
))
_GROUP_EDIT = frozenset(('setwd', 'assign', 'pipe', 'outline'))
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


def filter_toolbar_rows(tb_rows, show_keys):
    """Filter _TB-like rows: leading sep + visibles + mid seps between groups.

    tb_rows: iterable of (name, hint, method, icon); method is None for seps.
    show_keys: iterable of action ids. Explicit empty → no buttons.
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
    """Filter side (name, cap, method, icon) rows — no separators."""
    if show_keys is None:
        show = set(DEFAULT_SHOW)
    else:
        keys = tuple(show_keys)
        if not keys:
            return ()
        show = set(parse_show(','.join(keys), default=()))
    return tuple(row for row in side_rows if row[0] in show)
