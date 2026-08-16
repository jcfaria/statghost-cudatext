# Document outline — RStudio / vscode-R lite (no LSP).
# Pure Python (no cudatext) so unit tests can run headless.
# Headers: # ---- / ## Title / # === ; functions: name <- function(
# Also light Python/Julia defs for multi-engine classrooms.

from __future__ import annotations

import re

_RE_SECTION = re.compile(
    r'^\s*#\s*(?:'
    r'[-*=]{3,}\s*(.*?)\s*[-*=]*'  # # ---- Title ----  or  # ====
    r'|(#{1,6})\s+(.+?)'             # ## Title / ### Title
    r')\s*$'
)
_RE_R_FUN = re.compile(
    r'^\s*([.`\w]+|`[^`]+`)\s*(?:<-|=)\s*function\s*\('
)
_RE_PY = re.compile(
    r'^\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)\s*[(:]'
)
_RE_JL = re.compile(
    r'^\s*(?:function|macro|struct|mutable\s+struct)\s+([A-Za-z_!][\w!]*)'
)


def _clean_title(s):
    t = (s or '').strip()
    t = t.strip('-*= \t')
    return t


def collect_outline(get_line, n):
    """Return list of dicts: {line, kind, title, depth}.

    kind: 'section' | 'function'
    line: 0-based index
    depth: 1..6 for markdown-ish headers; 0 for #---- ; 1 for functions
    """
    out = []
    if n is None or n < 0:
        return out
    for i in range(int(n)):
        raw = get_line(i) if get_line else ''
        if raw is None:
            raw = ''
        m = _RE_SECTION.match(raw)
        if m:
            if m.group(1) is not None:
                title = _clean_title(m.group(1)) or 'section'
                depth = 0
            else:
                hashes = m.group(2) or '#'
                title = _clean_title(m.group(3)) or 'section'
                depth = len(hashes)
            out.append({
                'line': i,
                'kind': 'section',
                'title': title,
                'depth': depth,
            })
            continue
        m = _RE_R_FUN.match(raw)
        if m:
            out.append({
                'line': i,
                'kind': 'function',
                'title': m.group(1),
                'depth': 1,
            })
            continue
        m = _RE_PY.match(raw)
        if m:
            out.append({
                'line': i,
                'kind': 'function',
                'title': m.group(1),
                'depth': 1,
            })
            continue
        m = _RE_JL.match(raw)
        if m:
            out.append({
                'line': i,
                'kind': 'function',
                'title': m.group(1),
                'depth': 1,
            })
            continue
    return out


def format_caption(item, width=48):
    """One list line for dlg_menu / side panel."""
    if not item:
        return ''
    kind = item.get('kind') or 'section'
    title = item.get('title') or ''
    line = int(item.get('line') or 0) + 1
    depth = int(item.get('depth') or 0)
    if kind == 'function':
        prefix = 'ƒ '
        pad = '  '
    else:
        prefix = '§ '
        pad = '  ' * max(0, min(depth, 4))
    body = pad + prefix + title
    suffix = '  L' + str(line)
    keep = max(12, width - len(suffix))
    if len(body) > keep:
        body = body[: keep - 1] + '…'
    return body + suffix
