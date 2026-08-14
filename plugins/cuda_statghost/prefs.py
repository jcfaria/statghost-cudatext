# Shared plugin prefs (cuda_statghost.ini). Lives in CudaText settings/.
# Not STATghost Console chrome. [bar] vis is leftover from the retired strip.

from __future__ import annotations

import os

from cudatext import APP_DIR_SETTINGS
from cudatext import app_path
from cudatext import ini_read
from cudatext import ini_write

INI_NAME = 'cuda_statghost.ini'

# In-process cache — INI is source of truth on disk; cache avoids a stale
# read if the editor keeps an old handle, and makes Send see OK immediately.
_collapse_cache = None
_source_echo_cache = None
_source_encoding_cache = None
_pipe_cache = None


def ini_path():
    return os.path.join(app_path(APP_DIR_SETTINGS), INI_NAME)


def get_exe():
    return (ini_read(ini_path(), 'host', 'exe', '') or '').strip()


def set_exe(path):
    ini_write(ini_path(), 'host', 'exe', (path or '').strip())


def get_collapse():
    """Default on: send editor wraps as one Console line."""
    global _collapse_cache
    if _collapse_cache is not None:
        return bool(_collapse_cache)
    raw = ini_read(ini_path(), 'send', 'collapse', '1')
    if raw is None or str(raw).strip() == '':
        raw = '1'
    _collapse_cache = str(raw).strip() == '1'
    return bool(_collapse_cache)


def set_collapse(on):
    global _collapse_cache
    _collapse_cache = bool(on)
    ini_write(ini_path(), 'send', 'collapse', '1' if on else '0')


def get_source_echo():
    """Default on: source(.path, echo=TRUE, …) for Source file."""
    global _source_echo_cache
    if _source_echo_cache is not None:
        return bool(_source_echo_cache)
    raw = ini_read(ini_path(), 'send', 'source_echo', '1')
    if raw is None or str(raw).strip() == '':
        raw = '1'
    _source_echo_cache = str(raw).strip() == '1'
    return bool(_source_echo_cache)


def set_source_echo(on):
    global _source_echo_cache
    _source_echo_cache = bool(on)
    ini_write(ini_path(), 'send', 'source_echo', '1' if on else '0')


def get_source_encoding():
    """Default UTF-8 — matches STATghost R EvalCode encoding."""
    global _source_encoding_cache
    if _source_encoding_cache is not None:
        return str(_source_encoding_cache)
    raw = ini_read(ini_path(), 'send', 'source_encoding', 'UTF-8')
    if raw is None or str(raw).strip() == '':
        raw = 'UTF-8'
    _source_encoding_cache = str(raw).strip()
    return str(_source_encoding_cache)


def set_source_encoding(enc):
    global _source_encoding_cache
    e = (enc or '').strip() or 'UTF-8'
    _source_encoding_cache = e
    ini_write(ini_path(), 'send', 'source_encoding', e)


def get_pipe_token():
    """Default native R pipe `|>` (R 4.1+); magrittr via Config."""
    global _pipe_cache
    if _pipe_cache is not None:
        return str(_pipe_cache)
    raw = ini_read(ini_path(), 'edit', 'pipe', 'native')
    if raw is None or str(raw).strip() == '':
        raw = 'native'
    key = str(raw).strip().lower()
    if key in ('magrittr', '%>%', 'tee'):
        _pipe_cache = '%>%'
    else:
        _pipe_cache = '|>'
    return str(_pipe_cache)


def set_pipe_token(kind):
    """kind: 'native' | 'magrittr' (or the tokens themselves)."""
    global _pipe_cache
    key = (kind or '').strip().lower()
    if key in ('magrittr', '%>%', 'tee'):
        ini_write(ini_path(), 'edit', 'pipe', 'magrittr')
        _pipe_cache = '%>%'
    else:
        ini_write(ini_path(), 'edit', 'pipe', 'native')
        _pipe_cache = '|>'


def encoding_for_r(enc=None):
    """Map CudaText / prefs name to what R `source(..., encoding=)` expects."""
    if enc is None:
        enc = get_source_encoding()
    n = (enc or '').strip()
    if not n:
        return 'UTF-8'
    key = n.lower().replace('_', '-')
    if key in ('utf-8', 'utf8', 'utf-8 bom', 'utf8 bom', 'utf-8 with bom'):
        return 'UTF-8'
    if key in ('latin1', 'latin-1', 'iso-8859-1'):
        return 'latin1'
    if key in ('utf-16 le', 'utf-16le', 'utf16le'):
        return 'UTF-16LE'
    if key in ('utf-16 be', 'utf-16be', 'utf16be'):
        return 'UTF-16BE'
    return n
