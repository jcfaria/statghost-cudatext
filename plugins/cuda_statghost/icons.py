# Tint monochrome toolbar glyphs to the current CudaText UI theme.
# Source PNGs stay black-on-transparent (Flaticon). Brand artwork is
# not passed through here. Stdlib only — CudaText has no Pillow.

from __future__ import annotations

import os
import struct
import zlib

from cudatext import APP_DIR_SETTINGS
from cudatext import PROC_THEME_UI_DICT_GET
from cudatext import PROC_THEME_UI_GET
from cudatext import app_path
from cudatext import app_proc

_PNG_SIG = b'\x89PNG\r\n\x1a\n'


def theme_rgb():
    """ButtonFont as (r, g, b). Theme dict color is LCL TColor (BGR)."""
    d = app_proc(PROC_THEME_UI_DICT_GET, '') or {}
    item = d.get('ButtonFont') or {}
    c = item.get('color')
    if not isinstance(c, int):
        return (0x90, 0x90, 0x90)
    return (c & 0xFF, (c >> 8) & 0xFF, (c >> 16) & 0xFF)


def theme_tag():
    name = app_proc(PROC_THEME_UI_GET, '') or 'theme'
    safe = ''.join(
        ch if ch.isalnum() or ch in '-_' else '_' for ch in str(name)
    )
    r, g, b = theme_rgb()
    return '%s_%02x%02x%02x' % (safe, r, g, b)


def cache_dir():
    d = os.path.join(app_path(APP_DIR_SETTINGS), 'cuda_statghost_icons')
    os.makedirs(d, exist_ok=True)
    return d


def tinted_path(src_path, rgb=None):
    """Write a themed copy next to settings; return that path."""
    if rgb is None:
        rgb = theme_rgb()
    base = os.path.basename(src_path)
    out = os.path.join(cache_dir(), theme_tag() + '_' + base)
    if os.path.isfile(out) and os.path.getmtime(out) >= os.path.getmtime(src_path):
        return out
    w, h, pix = _read_rgba(src_path)
    tr, tg, tb = rgb
    for i in range(0, len(pix), 4):
        if pix[i + 3] == 0:
            continue
        pix[i] = tr
        pix[i + 1] = tg
        pix[i + 2] = tb
    _write_rgba(out, w, h, pix)
    return out


def _read_rgba(path):
    data = open(path, 'rb').read()
    if data[:8] != _PNG_SIG:
        raise ValueError('not a PNG: ' + path)
    w = h = bit = ctype = inter = None
    idat = []
    i = 8
    n = len(data)
    while i + 8 <= n:
        ln = struct.unpack('>I', data[i:i + 4])[0]
        typ = data[i + 4:i + 8]
        chunk = data[i + 8:i + 8 + ln]
        i += 12 + ln
        if typ == b'IHDR':
            w, h, bit, ctype, _c, _f, inter = struct.unpack('>IIBBBBB', chunk)
        elif typ == b'IDAT':
            idat.append(chunk)
        elif typ == b'IEND':
            break
    if w is None or bit != 8 or inter != 0 or ctype != 6:
        raise ValueError('need 8-bit RGBA PNG: ' + path)
    raw = zlib.decompress(b''.join(idat))
    return w, h, _unfilter(w, h, 4, raw)


def _unfilter(w, h, bpp, raw):
    stride = w * bpp
    out = bytearray(stride * h)
    i = 0
    prev = bytearray(stride)
    for y in range(h):
        ft = raw[i]
        i += 1
        row = bytearray(raw[i:i + stride])
        i += stride
        if ft == 1:
            for x in range(stride):
                left = row[x - bpp] if x >= bpp else 0
                row[x] = (row[x] + left) & 255
        elif ft == 2:
            for x in range(stride):
                row[x] = (row[x] + prev[x]) & 255
        elif ft == 3:
            for x in range(stride):
                left = row[x - bpp] if x >= bpp else 0
                row[x] = (row[x] + ((left + prev[x]) // 2)) & 255
        elif ft == 4:
            for x in range(stride):
                left = row[x - bpp] if x >= bpp else 0
                up = prev[x]
                ul = prev[x - bpp] if x >= bpp else 0
                p = left + up - ul
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - ul)
                pr = left if pa <= pb and pa <= pc else (up if pb <= pc else ul)
                row[x] = (row[x] + pr) & 255
        elif ft != 0:
            raise ValueError('bad PNG filter %d' % ft)
        out[y * stride:(y + 1) * stride] = row
        prev = row
    return out


def _write_rgba(path, w, h, pix):
    stride = w * 4
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(pix[y * stride:(y + 1) * stride])
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)
    idat = zlib.compress(bytes(raw), 9)
    buf = bytearray(_PNG_SIG)
    buf.extend(_chunk(b'IHDR', ihdr))
    buf.extend(_chunk(b'IDAT', idat))
    buf.extend(_chunk(b'IEND', b''))
    open(path, 'wb').write(buf)


def _chunk(typ, data):
    crc = zlib.crc32(typ)
    crc = zlib.crc32(data, crc) & 0xFFFFFFFF
    return struct.pack('>I', len(data)) + typ + data + struct.pack('>I', crc)
