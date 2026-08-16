# Extract essential Tinn-R_D imlTinnR 16px PNGs and upsample to 24/32.
# Stdlib only. Read-only vs Tinn-R_D. Output: w_todo/icons/{16,24,32}px/
#
# Usage (from repo root or this folder):
#   python extract_tinn_icons.py

from __future__ import annotations

import re
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'icons'
DFM = Path(
    r'C:\Users\jcfaria\Documents\GitHub\Tinn-R_D'
    r'\Tinn-R\source\Tinn-R\ufrmMain.dfm'
)

# SAP 01 §3.E — essential TBRMain indexes only.
INDEXES = {
    2: 'send_file',
    4: 'send_selection',
    12: 'send_smart',
    13: 'workdir',
    20: 'clear_console',
    36: 'set_workdir',
    271: 'send_contiguous',
    372: 'chunk_next',
    373: 'chunk_current',
    374: 'chunk_previous',
    375: 'chunk_menu',
}

_PNG_SIG = b'\x89PNG\r\n\x1a\n'
_ITEM_RE = re.compile(
    r'item\s+Background\s*=\s*clWindow\s+'
    r"Name\s*=\s*'PngImage(\d+)'\s+"
    r'PngImage\.Data\s*=\s*\{([0-9A-Fa-f\s]+)\}',
    re.MULTILINE,
)


def _hex_to_bytes(blob: str) -> bytes:
    hexes = re.sub(r'\s+', '', blob)
    return bytes.fromhex(hexes)


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _png_rgba(data: bytes):
    if not data.startswith(_PNG_SIG):
        raise ValueError('not a png')
    pos = 8
    width = height = None
    raw = b''
    while pos + 8 <= len(data):
        length = struct.unpack('>I', data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b'IHDR':
            width, height, bit, color, comp, filt, inter = struct.unpack(
                '>IIBBBBB', chunk
            )
            if (bit, color, comp, filt, inter) != (8, 6, 0, 0, 0):
                raise ValueError(
                    'need 8-bit RGBA non-interlaced (got %s)' % (
                        (bit, color, comp, filt, inter),
                    )
                )
        elif ctype == b'IDAT':
            raw += chunk
        elif ctype == b'IEND':
            break
    if width is None:
        raise ValueError('no IHDR')
    body = zlib.decompress(raw)
    stride = width * 4
    rows = []
    i = 0
    prev = bytearray(stride)
    for _y in range(height):
        ftype = body[i]
        i += 1
        row = bytearray(body[i:i + stride])
        i += stride
        if ftype == 0:
            pass
        elif ftype == 1:
            for x in range(stride):
                left = row[x - 4] if x >= 4 else 0
                row[x] = (row[x] + left) & 255
        elif ftype == 2:
            for x in range(stride):
                row[x] = (row[x] + prev[x]) & 255
        elif ftype == 4:
            for x in range(stride):
                left = row[x - 4] if x >= 4 else 0
                up = prev[x]
                ul = prev[x - 4] if x >= 4 else 0
                row[x] = (row[x] + _paeth(left, up, ul)) & 255
        else:
            raise ValueError('filter %s' % ftype)
        rows.append(bytes(row))
        prev = row
    return width, height, rows


def _pack_png(width, height, rows):
    raw = bytearray()
    for row in rows:
        raw.append(0)
        raw.extend(row)
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)

    def chunk(tag, payload):
        crc = zlib.crc32(tag)
        crc = zlib.crc32(payload, crc) & 0xFFFFFFFF
        return struct.pack('>I', len(payload)) + tag + payload + struct.pack(
            '>I', crc
        )

    return (
        _PNG_SIG
        + chunk(b'IHDR', ihdr)
        + chunk(b'IDAT', zlib.compress(bytes(raw), 9))
        + chunk(b'IEND', b'')
    )


def _resize_nn(width, height, rows, out_w, out_h):
    out = []
    for y in range(out_h):
        sy = min(height - 1, y * height // out_h)
        src = rows[sy]
        row = bytearray(out_w * 4)
        for x in range(out_w):
            sx = min(width - 1, x * width // out_w)
            o = x * 4
            i = sx * 4
            row[o:o + 4] = src[i:i + 4]
        out.append(bytes(row))
    return out


def main():
    text = DFM.read_text(encoding='latin-1', errors='replace')
    found = {}
    for match in _ITEM_RE.finditer(text):
        idx = int(match.group(1))
        found[idx] = _hex_to_bytes(match.group(2))
    if not found:
        raise SystemExit('no PngImage items in %s' % DFM)
    missing = [i for i in INDEXES if i not in found]
    if missing:
        raise SystemExit('missing indexes: %s (have 0..%s)' % (
            missing, max(found),
        ))
    for folder in ('16px', '24px', '32px'):
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    for idx, stem in INDEXES.items():
        blob = found[idx]
        w, h, rows = _png_rgba(blob)
        (OUT / '16px' / ('%s.png' % stem)).write_bytes(blob)
        for px in (24, 32):
            scaled = _resize_nn(w, h, rows, px, px)
            (OUT / ('%spx' % px) / ('%s.png' % stem)).write_bytes(
                _pack_png(px, px, scaled)
            )
        print('ok %s  (index %s, %sx%s)' % (stem, idx, w, h))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
