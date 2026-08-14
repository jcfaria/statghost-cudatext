# Pure icon FG picker (no CudaText import) — unit-tested in test_unit.py.
# Used by icons.py for theme-aware toolbar / side-tab tint.

from __future__ import annotations

_FG_LIGHT = (0xE8, 0xE8, 0xE8)
_FG_DARK = (0x20, 0x20, 0x20)
_MIN_CONTRAST = 3.0
_MODES = ('auto', 'light', 'dark', 'theme')


def clamp_mode(raw):
    key = (raw or '').strip().lower()
    if key in _MODES:
        return key
    return 'auto'


def rel_luma(rgb):
    """Relative luminance (sRGB, 0..1)."""
    r, g, b = rgb
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def contrast_ratio(fg, bg):
    """WCAG contrast ratio of two (r,g,b) tuples."""
    l1 = rel_luma(fg)
    l2 = rel_luma(bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def pick_fg_rgb(mode, button_font, bg, candidates=None):
    """Pick homogeneous icon FG for toolbar + side tab.

    mode: auto | light | dark | theme
    candidates: optional extra theme fonts tried under auto.
    """
    mode = clamp_mode(mode)
    if mode == 'light':
        return _FG_LIGHT
    if mode == 'dark':
        return _FG_DARK
    if mode == 'theme':
        return button_font

    ordered = [button_font]
    if candidates:
        for c in candidates:
            if c not in ordered:
                ordered.append(c)
    best = None
    best_ratio = 0.0
    for cand in ordered:
        r = contrast_ratio(cand, bg)
        if r >= _MIN_CONTRAST and r > best_ratio:
            best = cand
            best_ratio = r
    if best is not None:
        return best
    if rel_luma(bg) < 0.45:
        return _FG_LIGHT
    return _FG_DARK
