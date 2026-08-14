# Shared TEMP/STATghost path slots — twin of STATghostcom `.paths`.
# Must match library/STATghostcom_R/STATghostcom/R/zzz.R exactly
# (OS TEMP, not R session tempdir(); same basenames / indices).

from __future__ import annotations

import os
import sys

_WIN = sys.platform.startswith('win')

# 1-based indices (R vector); keep in sync with STATghostcom .onLoad.
IDX_ROOT = 1
IDX_FILE = 4
IDX_SELECTION = 5

_BASENAMES = (
    '',                    # 1
    'search.txt',          # 2
    'objects.txt',         # 3
    'file.R',              # 4
    'selection.R',         # 5
    'block.R',             # 6
    'lines.R',             # 7
    'reformat_input.R',    # 8
    'reformat_output.R',   # 9
    'mirrors.R',           # 10
    'code_completion.txt', # 11
)


def temp_root():
    """OS temp root — Windows TEMP/TMP, else /tmp (TinnRcom / companion)."""
    if _WIN:
        t = (os.environ.get('TEMP') or os.environ.get('TMP') or '').strip()
        if t:
            return t
        import tempfile
        return tempfile.gettempdir()
    return '/tmp'


def paths_dir():
    return os.path.join(temp_root(), 'STATghost')


def path_at(index_1based):
    """Absolute path for `.paths[index]` (1-based)."""
    i = int(index_1based) - 1
    if i < 0 or i >= len(_BASENAMES):
        raise IndexError('STATghost .paths index out of range: %s' % index_1based)
    base = _BASENAMES[i]
    root = paths_dir()
    if base == '':
        return root if root.endswith(os.sep) else root + os.sep
    return os.path.join(root, base)


def ensure_dir():
    os.makedirs(paths_dir(), exist_ok=True)
    return paths_dir()


def write_slot(index_1based, text, encoding='utf-8'):
    """Write text into a `.paths[n]` file. Returns the absolute path."""
    ensure_dir()
    path = path_at(index_1based)
    if index_1based == IDX_ROOT:
        raise ValueError('cannot write the .paths root slot')
    data = text if text is not None else ''
    # Normalize newlines for R source() on all platforms.
    data = data.replace('\r\n', '\n').replace('\r', '\n')
    with open(path, 'w', encoding=encoding, newline='\n') as f:
        f.write(data)
    return path
