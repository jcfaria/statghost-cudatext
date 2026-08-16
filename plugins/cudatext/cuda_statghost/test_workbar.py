#!/usr/bin/env python3
# Workbar battery (VP-WB-1 / WB-5). Layers:
#   A static  — nests, glyphs, install.inf methods, rword payloads
#   B live SG — clipboard EVAL → STATghost clip.R (gentle cycle)
#   C live Cuda — open sample + Ctrl+Enter (plugin Send)
#
# Default cycle is gentle: no Config, no Quit, no rm, no plot/help.
# Full destructive: STATGHOST_WORKBAR_TF=full
#
#   python test_workbar.py -v

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import chrome_show  # noqa: E402
import host  # noqa: E402
import paths  # noqa: E402
import protocol  # noqa: E402
import rword  # noqa: E402

_SG = host.sibling_dir('statghost') or ''
SAMPLE = os.path.join(_SG, 'sample') if _SG else ''
SAMPLE_R = os.path.join(SAMPLE, 'R')
HELLO = os.path.join(SAMPLE_R, '01_hello.R')
_CUDA = host.sibling_dir('CudaText') or ''
CUDA_EXE = os.path.join(_CUDA, 'app', 'cudatext.exe') if _CUDA else ''
POLL_S = 0.12
EVAL_WAIT_S = 18.0
_WIN = sys.platform.startswith('win')
_FULL = (os.environ.get('STATGHOST_WORKBAR_TF') or '').strip().lower() in (
    '1', 'true', 'full', 'yes',
)
_CUDA = _FULL or (os.environ.get('STATGHOST_WORKBAR_TF') or '').strip().lower() in (
    'cuda', 'send',
)
COLOUR_PNG = (
    'ls.png', 'print.png', 'print_head.png', 'print_tail.png',
    'names.png', 'str.png', 'plot.png', 'help_selected.png',
    'close_graphics.png', 'remove_objects.png', 'clear_all.png',
    'sweave.png', 'knit.png', 'knit-html.png',
)


def _inf_methods():
    with open(os.path.join(HERE, 'install.inf'), encoding='utf-8') as fh:
        return set(re.findall(r'(?m)^method=(\w+)\s*$', fh.read()))


def _clip_r():
    pids = host.list_pids()
    if not pids:
        return ''
    return os.path.join(paths.temp_root(), 'statghost_%s' % pids[0], 'clip.R')


def _read(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return fh.read()
    except OSError:
        return ''


def _set_clip(text):
    data = text if isinstance(text, str) else str(text or '')
    if _WIN:
        return _set_clip_win(data)
    for tool, args in (
        ('xclip', ['xclip', '-selection', 'clipboard', '-in']),
        ('wl-copy', ['wl-copy']),
        ('xsel', ['xsel', '--clipboard', '--input']),
    ):
        try:
            p = subprocess.Popen(
                args, stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            p.communicate(input=data.encode('utf-8'), timeout=2)
            return True
        except (OSError, subprocess.TimeoutExpired):
            continue
    return False


def _set_clip_win(text):
    import ctypes
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    data = str(text or '')
    for _attempt in range(8):
        if user32.OpenClipboard(None):
            break
        time.sleep(0.05)
    else:
        return _set_clip_win_ps(data)
    try:
        user32.EmptyClipboard()
        nbytes = (len(data) + 1) * ctypes.sizeof(ctypes.c_wchar)
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, nbytes)
        if not handle:
            return False
        locked = kernel32.GlobalLock(handle)
        if not locked:
            kernel32.GlobalFree(handle)
            return False
        ctypes.memmove(locked, ctypes.create_unicode_buffer(data), nbytes)
        kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            kernel32.GlobalFree(handle)
            return False
        return True
    except OSError:
        return _set_clip_win_ps(data)
    finally:
        user32.CloseClipboard()


def _set_clip_win_ps(text):
    """Fallback: PowerShell Set-Clipboard (UTF-16)."""
    try:
        p = subprocess.run(
            [
                'powershell', '-NoProfile', '-STA', '-Command',
                'Set-Clipboard -Value ([Console]::In.ReadToEnd())',
            ],
            input=text if isinstance(text, str) else str(text or ''),
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=8,
        )
        return p.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _arm():
    return _set_clip(protocol.make_command(protocol.CMD_ARM))


def _eval(code):
    msg = protocol.make_eval(code)
    if not _set_clip(msg):
        return False, msg
    return True, msg


def _wait_clip(needle, timeout=EVAL_WAIT_S):
    path = _clip_r()
    last = ''
    deadline = time.time() + timeout
    while time.time() < deadline:
        last = _read(path)
        if needle in last:
            return True, last
        time.sleep(POLL_S)
    return False, last


def _cuda_hwnd():
    if not _WIN:
        return None
    import ctypes
    user32 = ctypes.windll.user32
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def _cb(hwnd, _lp):
        if not user32.IsWindowVisible(hwnd):
            return True
        n = user32.GetWindowTextLengthW(hwnd)
        if n <= 0:
            return True
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        if 'CudaText' in (buf.value or ''):
            found.append(hwnd)
        return True

    user32.EnumWindows(_cb, 0)
    return found[0] if found else None


def _focus_cuda():
    hwnd = _cuda_hwnd()
    if not hwnd:
        return False
    import ctypes
    user32 = ctypes.windll.user32
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.35)
    return int(user32.GetForegroundWindow()) == int(hwnd)


def _send_chord(vks):
    import ctypes

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = (
            ('wVk', ctypes.c_ushort),
            ('wScan', ctypes.c_ushort),
            ('dwFlags', ctypes.c_ulong),
            ('time', ctypes.c_ulong),
            ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong)),
        )

    class INPUT(ctypes.Structure):
        class _I(ctypes.Union):
            _fields_ = (('ki', KEYBDINPUT),)
        _anonymous_ = ('i',)
        _fields_ = (('type', ctypes.c_ulong), ('i', _I))

    KEYEVENTF_KEYUP = 0x0002
    INPUT_KEYBOARD = 1
    extra = ctypes.c_ulong(0)

    def fire(vk, up=False):
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.ki.wVk = vk
        inp.ki.dwFlags = KEYEVENTF_KEYUP if up else 0
        inp.ki.dwExtraInfo = ctypes.pointer(extra)
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    for vk in vks:
        fire(vk, False)
    time.sleep(0.05)
    for vk in reversed(vks):
        fire(vk, True)


class TestWorkbarStatic(unittest.TestCase):
    def test_nests_and_default_toolbar(self):
        show = chrome_show.DEFAULT_SHOW
        self.assertEqual(
            chrome_show.nest_menu_keys('send', show),
            ('function', 'above', 'below', 'chunk'),
        )
        self.assertEqual(
            chrome_show.nest_menu_keys('source', show),
            ('srcsel', 'setwd'),
        )
        self.assertEqual(
            chrome_show.nest_menu_keys('inspect', show),
            ('ls', 'str', 'names', 'plot', 'help', 'head', 'tail'),
        )
        self.assertEqual(
            chrome_show.nest_menu_keys('clear', show),
            ('close_graphics', 'remove_objects', 'clear_all'),
        )
        tb = (
            ('sep', '-', None, None),
            ('cfg', 'c', 'config', 'a.png'),
            ('arm', 'a', 'toggle_arm', 'a.png'),
            ('host', 'h', 'toggle_host', 'h.png'),
            ('sep_send', '-', None, None),
            ('send', 's', 'send_selection', 's.png'),
            ('function', 'f', 'send_function', 'f.png'),
            ('above', 'b', 'send_above', 'b.png'),
            ('below', 'w', 'send_below', 'w.png'),
            ('chunk', 'k', 'send_chunk', 'k.png'),
            ('source', 'o', 'send_file', 'o.png'),
            ('srcsel', 'r', 'source_selection', 'r.png'),
            ('setwd', 'd', 'set_wd_here', 'd.png'),
            ('inspect', 'i', 'inspect_print', 'i.png'),
            ('ls', 'l', 'inspect_ls', 'l.png'),
            ('str', 't', 'inspect_str', 't.png'),
            ('names', 'n', 'inspect_names', 'n.png'),
            ('plot', 'p', 'inspect_plot', 'p.png'),
            ('help', 'e', 'inspect_help', 'e.png'),
            ('head', 'hd', 'inspect_head', 'hd.png'),
            ('tail', 'tl', 'inspect_tail', 'tl.png'),
            ('clear', 'x', 'clear_console', 'x.png'),
            ('close_graphics', 'g', 'inspect_graphics_off', 'g.png'),
            ('remove_objects', 'rm', 'inspect_rm_all', 'rm.png'),
            ('clear_all', 'ca', 'inspect_clear_all', 'ca.png'),
            ('sep_edit', '-', None, None),
            ('assign', 'as', 'insert_assign', 'as.png'),
            ('pipe', 'pi', 'insert_pipe', 'pi.png'),
            ('outline', 'ou', 'show_outline', 'ou.png'),
        )
        rows = chrome_show.collapse_nested_rows(
            chrome_show.filter_toolbar_rows(tb, show),
        )
        names = [r[0] for r in rows]
        self.assertEqual(
            names,
            ['sep', 'cfg', 'arm', 'host', 'sep_send',
             'send', 'source', 'inspect', 'clear'],
        )
        self.assertEqual(
            chrome_show.side_keys(show),
            ('cfg', 'arm', 'host', 'send', 'source', 'inspect', 'clear'),
        )

    def test_cli_allowlist_in_install_inf(self):
        inf = _inf_methods()
        missing = sorted(chrome_show.CLI_METHODS - inf)
        self.assertEqual(missing, [], 'CLI methods missing in install.inf')
        self.assertTrue(
            chrome_show.CYCLE_METHODS <= chrome_show.CLI_METHODS,
        )
        banned = {'config', 'toggle_host', 'toggle_arm', 'show_outline'}
        self.assertFalse(chrome_show.CLI_METHODS & banned)

    def test_colour_glyphs_16_24_32(self):
        png = os.path.join(HERE, 'png')
        missing = []
        for px in ('16px', '24px', '32px'):
            for name in COLOUR_PNG:
                path = os.path.join(png, px, name)
                if not os.path.isfile(path):
                    missing.append(path)
        self.assertEqual(missing, [])

    def test_rword_workbar_payloads(self):
        self.assertEqual(rword.wrap_code('str', 'iris'), 'str(iris)')
        self.assertEqual(rword.wrap_code('names', 'iris'), 'names(iris)')
        self.assertEqual(rword.wrap_code('head', 'iris'), 'head(iris)')
        self.assertEqual(rword.wrap_code('tail', 'iris'), 'tail(iris)')
        self.assertEqual(rword.help_code('iris'), 'help(iris)')
        self.assertEqual(rword.print_target('', '  iris', 2), 'iris')
        self.assertEqual(rword.wrap_code('str', ''), '')
        self.assertEqual(rword.help_code('iris$x'), '')


class TestWorkbarLiveSG(unittest.TestCase):
    """Clipboard → Armed STATghost. Leaves the session up."""

    @classmethod
    def setUpClass(cls):
        if not host.is_running():
            raise unittest.SkipTest('STATghost is not running')
        if _WIN:
            ok = _set_clip('cuda_statghost workbar tf probe')
            if not ok:
                raise unittest.SkipTest('could not write Windows clipboard')
        elif not os.environ.get('DISPLAY'):
            raise unittest.SkipTest('DISPLAY unset and not Windows')
        if not _arm():
            raise unittest.SkipTest('could not put ARM on the clipboard')
        time.sleep(0.5)
        cls.clip = _clip_r()

    def _land(self, code, needle=None):
        """EVAL *code*; clip.R must contain a unique stamp (overlapping tests)."""
        stamp = '# WBTF ' + protocol._nonce()
        body = (code if code is not None else '') + '\n' + stamp
        needle = needle if needle is not None else code
        _arm()
        time.sleep(0.35)
        ok, _ = _eval(body)
        self.assertTrue(ok, 'clipboard EVAL failed for %r' % code)
        found, last = _wait_clip(stamp, timeout=EVAL_WAIT_S)
        self.assertTrue(
            found,
            'clip.R missing stamp %r / payload %r\npath=%s\n---\n%s'
            % (stamp, needle, self.clip, last[:500]),
        )
        self.assertIn(needle, last)

    def test_01_ls(self):
        self._land('ls()')

    def test_02_print_pi(self):
        self._land('pi')

    def test_03_str_letters(self):
        self._land('str(letters)')

    def test_04_names_iris(self):
        self._land(rword.wrap_code('names', 'iris'))

    def test_05_head_iris(self):
        self._land('head(iris, 2)')

    def test_06_tail_iris(self):
        self._land('tail(iris, 2)')

    def test_07_graphics_off(self):
        self._land('graphics.off()')

    def test_08_clear_token_not_eval(self):
        tag = 'wb_clear_%s' % protocol._nonce()
        marker = os.path.join(paths.paths_dir(), 'cuda_plugin_tf_%s.txt' % tag)
        self.assertTrue(_set_clip(protocol.make_command(protocol.CMD_CLEAR)))
        time.sleep(0.6)
        self.assertFalse(os.path.isfile(marker), 'CLEAR must not eval')

    @unittest.skipUnless(_FULL, 'set STATGHOST_WORKBAR_TF=full')
    def test_09_plot_iris(self):
        self._land(rword.wrap_code('plot', 'iris'))

    @unittest.skipUnless(_FULL, 'set STATGHOST_WORKBAR_TF=full')
    def test_10_help_iris(self):
        self._land(rword.help_code('iris'))


@unittest.skipUnless(_CUDA, 'set STATGHOST_WORKBAR_TF=cuda to send Ctrl+Enter')
class TestWorkbarLiveCuda(unittest.TestCase):
    """Open sample in the running CudaText and fire plugin Send (Ctrl+Enter)."""

    @classmethod
    def setUpClass(cls):
        if not host.is_running():
            raise unittest.SkipTest('STATghost is not running')
        if not os.path.isfile(HELLO):
            raise unittest.SkipTest('sample 01_hello.R missing')
        if not _WIN:
            raise unittest.SkipTest('Cuda hotkey layer is Windows-only here')
        if not os.path.isfile(CUDA_EXE):
            raise unittest.SkipTest('cudatext.exe not found')
        if not _cuda_hwnd():
            raise unittest.SkipTest('CudaText window not found')
        cls.clip = _clip_r()

    def test_01_send_hello_one_plus_one(self):
        _arm()
        time.sleep(0.3)
        subprocess.Popen(
            [CUDA_EXE, '%s@7' % HELLO],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + 8.0
        while time.time() < deadline:
            time.sleep(0.15)
        self.assertTrue(_focus_cuda(), 'could not focus CudaText')
        VK_ESCAPE = 0x1B
        VK_CONTROL = 0x11
        VK_RETURN = 0x0D
        _send_chord((VK_ESCAPE,))
        time.sleep(0.08)
        _send_chord((VK_CONTROL, VK_RETURN))
        found, last = _wait_clip('1 + 1', timeout=10.0)
        self.assertTrue(
            found,
            'Send (Ctrl+Enter) did not put 1 + 1 into clip.R\n---\n%s'
            % last[:400],
        )


if __name__ == '__main__':
    print(
        'workbar: sg=%s clip=%s cuda=%s full=%s'
        % (host.list_pids(), _clip_r(), os.path.isfile(CUDA_EXE), _FULL),
        flush=True,
    )
    unittest.main(verbosity=2)
