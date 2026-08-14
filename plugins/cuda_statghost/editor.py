# CudaText caret / selection helpers. No STATghost protocol here.

from cudatext import ed


def caret_line_index():
    carets = ed.get_carets()
    if not carets:
        return None
    _x, y, _x2, _y2 = carets[0]
    if y < 0:
        return None
    return y


def selection_text():
    sel = ed.get_text_sel()
    if sel:
        return sel
    return ''


def get_line(i):
    t = ed.get_text_line(i)
    return t if t else ''


def line_count():
    return ed.get_line_count()


def line_text(y):
    if y is None:
        return ''
    return get_line(y)


def is_blank_or_hash_comment(line):
    s = (line or '').strip()
    return s == '' or s.startswith('#')


def selection_last_line():
    """Last line index of a real selection, or None."""
    carets = ed.get_carets()
    if not carets:
        return None
    x, y, x2, y2 = carets[0]
    if x2 < 0:
        return None
    if (y, x) <= (y2, x2):
        ay, bx, by = y, x2, y2
    else:
        ay, bx, by = y2, x, y
    last = by
    if bx == 0 and by > ay:
        last = by - 1
    return last


def advance_caret_after(from_y):
    """Col 0 of next code line; skip blanks and # comments. EOF: stay."""
    n = ed.get_line_count()
    y = from_y + 1
    while y < n:
        if not is_blank_or_hash_comment(ed.get_text_line(y)):
            ed.set_caret(0, y)
            return
        y += 1


def skip_to_code_line(y):
    """If caret is on blank/#, start at the next code line (sniper chunk)."""
    n = ed.get_line_count()
    if y is None:
        return None
    while y < n and is_blank_or_hash_comment(ed.get_text_line(y)):
        y += 1
    if y >= n:
        return None
    return y
