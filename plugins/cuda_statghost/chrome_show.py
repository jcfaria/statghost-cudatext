# Shared toolbar / side-tab visibility (pure — no CudaText).
# One show-list for both bars (golden rule: same actions, same order).

from __future__ import annotations

# Canonical action ids — order matches chrome._TB (minus separators).
ACTION_KEYS = ('cfg', 'arm', 'host', 'send', 'source', 'clear')
DEFAULT_SHOW = ACTION_KEYS

# Host group vs editor group — separator between if both have visibles.
_GROUP_HOST = frozenset(('cfg', 'arm', 'host'))
_GROUP_SEND = frozenset(('send', 'source', 'clear'))


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
    # Stable classroom order (not CSV order).
    return tuple(k for k in ACTION_KEYS if k in parts)


def format_show(keys):
    """CSV for ini — only known keys, canonical order."""
    return ','.join(parse_show(','.join(keys or ())))


def filter_toolbar_rows(tb_rows, show_keys):
    """Filter _TB-like rows: keep leading sep + visibles + mid sep if needed.

    tb_rows: iterable of (name, hint, method, icon); method is None for seps.
    show_keys: iterable of action ids. Explicit empty → no buttons.
    """
    if show_keys is None:
        show = set(DEFAULT_SHOW)
    else:
        keys = tuple(show_keys)
        if not keys:
            return ()
        show = set(parse_show(','.join(keys)))
    actions = [
        row for row in tb_rows
        if row[2] is not None and row[0] in show
    ]
    if not actions:
        return ()
    g1 = [r for r in actions if r[0] in _GROUP_HOST]
    g2 = [r for r in actions if r[0] in _GROUP_SEND]
    out = []
    # Leading sep (gap after CudaText stock icons) when any action shows.
    if tb_rows and tb_rows[0][2] is None:
        out.append(tb_rows[0])
    out.extend(g1)
    if g1 and g2:
        mid = None
        for row in tb_rows:
            if row[2] is None and row[0] != tb_rows[0][0]:
                mid = row
                break
        if mid is None:
            mid = ('sep_send', '-', None, None)
        out.append(mid)
    out.extend(g2)
    return tuple(out)


def filter_side_actions(side_rows, show_keys):
    """Filter side (name, cap, method, icon) rows — no separators."""
    if show_keys is None:
        show = set(DEFAULT_SHOW)
    else:
        keys = tuple(show_keys)
        if not keys:
            return ()
        show = set(parse_show(','.join(keys)))
    return tuple(row for row in side_rows if row[0] in show)
