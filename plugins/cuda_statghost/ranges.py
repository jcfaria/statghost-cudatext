# Range helpers for Send above / below / sniper chunk.
# Pure Python (no cudatext).

from __future__ import annotations


def lines_from_start(get_line, end_inclusive, n):
    """Text from line 0 through end_inclusive (0-based), inclusive."""
    if n is None or n <= 0:
        return ''
    last = int(end_inclusive)
    if last < 0:
        return ''
    if last >= n:
        last = n - 1
    parts = []
    for i in range(0, last + 1):
        parts.append(get_line(i) if get_line else '')
    return '\n'.join(parts)


def lines_to_end(get_line, start, n):
    """Text from start through EOF (0-based), inclusive."""
    if n is None or n <= 0:
        return ''
    first = int(start)
    if first < 0:
        first = 0
    if first >= n:
        return ''
    parts = []
    for i in range(first, n):
        parts.append(get_line(i) if get_line else '')
    return '\n'.join(parts)


def sniper_chunk_bounds(y, get_line, n, is_cut):
    """Blank/#-comment separated chunk containing line y (sniper style).

    is_cut(line) → True for blank or whole-line # comment.
    Returns (start, end) inclusive, or (None, None).
    """
    if y is None or n is None or n <= 0:
        return None, None
    y = int(y)
    if y < 0 or y >= n:
        return None, None
    # Expand to nearest code line if caret on a cut.
    while y < n and is_cut(get_line(y) if get_line else ''):
        y += 1
    if y >= n:
        return None, None
    start = y
    while start > 0 and not is_cut(get_line(start - 1) if get_line else ''):
        start -= 1
    end = y
    while end + 1 < n and not is_cut(get_line(end + 1) if get_line else ''):
        end += 1
    return start, end


def join_range(get_line, start, end):
    if start is None or end is None:
        return ''
    if end < start:
        return ''
    parts = []
    for i in range(int(start), int(end) + 1):
        parts.append(get_line(i) if get_line else '')
    return '\n'.join(parts)
