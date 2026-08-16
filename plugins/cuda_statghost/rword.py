# R identifier at caret / selection — Tinn fFindWord_Extended lite.
# Pure: no CudaText. Classroom refs: iris, stats::sd, iris$Sepal.Length.

from __future__ import annotations

import re

_REF = re.compile(
    r'^'
    r'[.A-Za-z][A-Za-z0-9._]*'
    r'(?:::[.A-Za-z][A-Za-z0-9._]*)?'
    r'(?:\$[.A-Za-z][A-Za-z0-9._]*)*'
    r'$'
)
_SPAN = set(
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:$'
)


def is_ref(text):
    """True if *text* is a sendable R name / pkg::fn / x$y chain."""
    s = (text or '').strip()
    if not s or ':::' in s:
        return False
    return _REF.match(s) is not None


def identifier_at(line, x):
    """Longest R ref spanning caret column *x* (0-based) on *line*."""
    s = line or ''
    n = len(s)
    if n == 0:
        return ''
    if x is None:
        x = 0
    x = max(0, min(int(x), n))
    if x < n and s[x] not in _SPAN and x > 0 and s[x - 1] in _SPAN:
        x -= 1
    if not ((x < n and s[x] in _SPAN) or (x > 0 and s[x - 1] in _SPAN)):
        return ''
    a = x
    while a > 0 and s[a - 1] in _SPAN:
        a -= 1
    b = x
    if b < n and s[b] not in _SPAN:
        b = x
    else:
        while b < n and s[b] in _SPAN:
            b += 1
    tok = s[a:b].strip(':$')
    if is_ref(tok):
        return tok
    return ''


def print_target(sel, line, x):
    """What Print sends: one-line selection, else identifier at caret."""
    raw = sel if sel is not None else ''
    if '\n' in raw or '\r' in raw:
        return identifier_at(line, x)
    s = raw.strip()
    if s:
        return s
    return identifier_at(line, x)


def wrap_target(sel, line, x):
    """What str/names/plot/head/tail wrap: must be a ref, else empty."""
    raw = sel if sel is not None else ''
    if '\n' not in raw and '\r' not in raw:
        s = raw.strip()
        if s:
            return s if is_ref(s) else ''
    return identifier_at(line, x)


def help_code(ref):
    """EVAL for Help (selected). Empty if ref cannot be a help topic."""
    if not is_ref(ref) or '$' in (ref or ''):
        return ''
    if '::' in ref:
        pkg, topic = ref.split('::', 1)
        if not pkg or not topic:
            return ''
        return "help(" + topic + ", package='" + pkg + "')"
    return 'help(' + ref + ')'


def wrap_code(fn, ref):
    """`fn(ref)` for head/str/plot/… — *fn* is a fixed classroom token."""
    if not is_ref(ref):
        return ''
    return fn + '(' + ref + ')'
