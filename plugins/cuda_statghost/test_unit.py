#!/usr/bin/env python3
# Automated unit checks for cuda_statghost (no CudaText host required).
# Run: python3 test_unit.py

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
import unittest

# Allow `python3 test_unit.py` from this folder or repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import paths  # noqa: E402
import protocol  # noqa: E402
import statement  # noqa: E402
import icons_fg  # noqa: E402
import chrome_show  # noqa: E402
import outline  # noqa: E402
import ranges  # noqa: E402


def _lines(text):
    rows = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    return rows


def _get(rows):
    def get_line(i):
        if i < 0 or i >= len(rows):
            return ''
        return rows[i]
    return get_line


class TestCollapseWraps(unittest.TestCase):
    def test_trailing_paren_joins(self):
        src = 'plot(\n  x\n)'
        out = statement.collapse_wraps(src)
        self.assertEqual(out.count('\n'), 0)
        self.assertIn('plot(', out)
        self.assertTrue(out.rstrip().endswith(')'))

    def test_operator_join(self):
        src = 'a <- 1 +\n  2'
        out = statement.collapse_wraps(src)
        self.assertEqual(out, 'a <- 1 + 2')

    def test_blank_chunk_cut(self):
        src = 'plot(x)\n\nabline(0, 1)'
        out = statement.collapse_wraps(src)
        self.assertEqual(out, src)

    def test_brace_block_keeps_statements(self):
        src = '''with(BOD, {
  plot(demand ~ Time,
       xlim = c(0, 8),
       ylim = c(0, 20),
       main = "sample 12 — BOD nls")
  points(predict(m_1) ~ Time,
         col = "red",
         pch = 19)
  lines(spline(predict(m_1) ~ Time, n = 200),
        col = "red",
        lwd = 2)
})'''
        out = statement.collapse_wraps(src)
        self.assertIn('\n', out)
        self.assertNotIn(') points', out)
        self.assertNotIn(') lines', out)
        self.assertIn('plot(demand ~ Time, xlim = c(0, 8)', out)
        self.assertIn('points(predict(m_1) ~ Time, col = "red", pch = 19)', out)
        self.assertTrue(out.rstrip().endswith('})'))

    def test_lone_close_paren_joins(self):
        src = 'plot(\n  x,\n  y\n)'
        out = statement.collapse_wraps(src)
        self.assertEqual(out, 'plot( x, y )')

    def test_deriv_wrap_joins_when_collapse_on(self):
        # Collapse ON: one Console line. Collapse OFF is identity in _send_code
        # (SG reprints wraps with `>`/`+`).
        src = 'deriv(fl,\n      c("a", "b"))'
        self.assertIn('\n', src)
        out = statement.collapse_wraps(src)
        self.assertEqual(out.count('\n'), 0)
        self.assertIn('deriv(fl,', out)
        self.assertIn('c("a", "b")', out)


class TestProtocol(unittest.TestCase):
    def test_eval_roundtrip(self):
        msg = protocol.make_eval('1 + 1')
        cmd, body = protocol.parse_message(msg)
        self.assertEqual(cmd, protocol.CMD_EVAL)
        self.assertEqual(body, '1 + 1')

    def test_clear_token(self):
        msg = protocol.make_command(protocol.CMD_CLEAR)
        cmd, body = protocol.parse_message(msg)
        self.assertEqual(cmd, protocol.CMD_CLEAR)
        self.assertEqual(body, '')

    def test_nonce_unique(self):
        a = protocol.make_command(protocol.CMD_ARM)
        b = protocol.make_command(protocol.CMD_ARM)
        self.assertNotEqual(a, b)


class TestPaths(unittest.TestCase):
    def test_slot4_basename(self):
        p = paths.path_at(paths.IDX_FILE)
        self.assertTrue(p.endswith('file.R'))
        self.assertIn('STATghost', p)

    def test_write_slot_roundtrip(self):
        root = paths.paths_dir()
        os.makedirs(root, exist_ok=True)
        text = 'x <- 1\n'
        path = paths.write_slot(paths.IDX_FILE, text)
        with open(path, encoding='utf-8') as f:
            self.assertEqual(f.read(), text)


class TestEnclosingFunction(unittest.TestCase):
    def test_r_caret_in_body(self):
        src = '''\
foo <- function(x) {
  y <- x + 1
  y
}
'''
        rows = _lines(src)
        # caret on "y <- x + 1"
        s, e = statement.enclosing_function(1, _get(rows), len(rows))
        self.assertEqual((s, e), (0, 3))
        text = statement.join_lines(_get(rows), s, e)
        self.assertIn('foo <- function', text)
        self.assertIn('y <- x + 1', text)

    def test_r_caret_on_closing_brace(self):
        src = '''\
foo <- function(x) {
  x
}
'''
        rows = _lines(src)
        s, e = statement.enclosing_function(2, _get(rows), len(rows))
        self.assertEqual((s, e), (0, 2))

    def test_r_nested_innermost(self):
        src = '''\
outer <- function(x) {
  inner <- function(y) {
    y + 1
  }
  inner(x)
}
'''
        rows = _lines(src)
        # inside inner body
        s, e = statement.enclosing_function(2, _get(rows), len(rows))
        self.assertEqual(s, 1)
        self.assertIn('inner <- function', rows[s])
        # on inner(x) — outside inner, inside outer
        s2, e2 = statement.enclosing_function(4, _get(rows), len(rows))
        self.assertEqual(s2, 0)
        self.assertIn('outer <- function', rows[s2])

    def test_r_equals_assign(self):
        src = '''\
f = function(a, b) {
  a + b
}
'''
        rows = _lines(src)
        s, e = statement.enclosing_function(1, _get(rows), len(rows))
        self.assertEqual(s, 0)

    def test_not_inside_function(self):
        src = 'x <- 1\ny <- 2\n'
        rows = _lines(src)
        s, e = statement.enclosing_function(1, _get(rows), len(rows))
        self.assertEqual((s, e), (None, None))

    def test_python_def(self):
        src = '''\
def foo(x):
    y = x + 1
    return y

z = 1
'''
        rows = _lines(src)
        s, e = statement.enclosing_function(1, _get(rows), len(rows))
        self.assertEqual(s, 0)
        self.assertEqual(e, 2)


class TestChromeShow(unittest.TestCase):
    def test_parse_default_and_order(self):
        self.assertEqual(chrome_show.parse_show(''), chrome_show.DEFAULT_SHOW)
        self.assertEqual(
            chrome_show.parse_show('clear,cfg,send'),
            ('cfg', 'send', 'clear'),
        )
        self.assertIn('function', chrome_show.ACTION_KEYS)

    def test_filter_keeps_mid_sep(self):
        tb = (
            ('sep', '-', None, None),
            ('cfg', 'c', 'config', 'a.png'),
            ('arm', 'a', 'toggle_arm', 'b.png'),
            ('sep_send', '-', None, None),
            ('send', 's', 'send_selection', 'c.png'),
            ('function', 'f', 'send_function', 'f.png'),
            ('clear', 'x', 'clear_console', 'd.png'),
            ('sep_edit', '-', None, None),
            ('outline', 'o', 'show_outline', 'o.png'),
        )
        rows = chrome_show.filter_toolbar_rows(tb, ('cfg', 'send', 'outline'))
        names = [r[0] for r in rows]
        self.assertEqual(
            names, ['sep', 'cfg', 'sep_send', 'send', 'sep_edit', 'outline'],
        )

    def test_filter_empty(self):
        tb = (
            ('sep', '-', None, None),
            ('cfg', 'c', 'config', 'a.png'),
        )
        self.assertEqual(chrome_show.filter_toolbar_rows(tb, ()), ())

    def test_side_filter(self):
        side = (
            ('cfg', 'Config', 'config', 'a.png'),
            ('send', 'Send', 'send_selection', 'b.png'),
            ('clear', 'Clear', 'clear_console', 'c.png'),
        )
        out = chrome_show.filter_side_actions(side, ('send',))
        self.assertEqual([r[0] for r in out], ['send'])


class TestIconFg(unittest.TestCase):
    def test_force_modes(self):
        bg = (0x1C, 0x1C, 0x1C)
        font = (0x44, 0x44, 0x44)
        self.assertEqual(icons_fg.pick_fg_rgb('light', font, bg), (0xE8, 0xE8, 0xE8))
        self.assertEqual(icons_fg.pick_fg_rgb('dark', font, bg), (0x20, 0x20, 0x20))
        self.assertEqual(icons_fg.pick_fg_rgb('theme', font, bg), font)

    def test_auto_rejects_dark_on_dark(self):
        bg = (0x1C, 0x1C, 0x1C)
        font = (0x44, 0x44, 0x44)
        fg = icons_fg.pick_fg_rgb('auto', font, bg)
        self.assertEqual(fg, (0xE8, 0xE8, 0xE8))
        self.assertGreaterEqual(icons_fg.contrast_ratio(fg, bg), 3.0)

    def test_auto_keeps_good_buttonfont(self):
        bg = (0x1C, 0x1C, 0x1C)
        font = (0xE0, 0xE0, 0xE0)
        self.assertEqual(icons_fg.pick_fg_rgb('auto', font, bg), font)


class TestOutline(unittest.TestCase):
    def test_sections_and_functions(self):
        src = '''\
# ---- Setup ----
x <- 1

## Model
fit <- function(y) {
  y
}
'''
        rows = _lines(src)
        items = outline.collect_outline(_get(rows), len(rows))
        kinds = [it['kind'] for it in items]
        self.assertIn('section', kinds)
        self.assertIn('function', kinds)
        titles = [it['title'] for it in items]
        self.assertTrue(any('Setup' in t or t == 'Setup' for t in titles))
        self.assertIn('fit', titles)


class TestRanges(unittest.TestCase):
    def test_above_below(self):
        rows = _lines('a\nb\nc\n')
        self.assertEqual(ranges.lines_from_start(_get(rows), 1, len(rows)), 'a\nb')
        self.assertEqual(ranges.lines_to_end(_get(rows), 1, len(rows)), 'b\nc\n')

    def test_sniper_chunk(self):
        rows = _lines('a <- 1\nb <- 2\n\nc <- 3\n')

        def is_cut(line):
            s = (line or '').strip()
            return s == '' or s.startswith('#')

        s, e = ranges.sniper_chunk_bounds(0, _get(rows), len(rows), is_cut)
        self.assertEqual((s, e), (0, 1))
        s2, e2 = ranges.sniper_chunk_bounds(3, _get(rows), len(rows), is_cut)
        self.assertEqual((s2, e2), (3, 3))


def _span(src, y):
    rows = _lines(src)
    s, e = statement.extend_statement(y, _get(rows), len(rows))
    return s, e, statement.dedent_block(statement.join_lines(_get(rows), s, e))


def _send_at(src, y):
    rows = _lines(src)
    n = len(rows)
    get = _get(rows)
    fs, fe = statement.enclosing_function(y, get, n)
    if fs is not None and fe is not None:
        text = statement.join_lines(get, fs, fe)
        return fs, fe, statement.dedent_block(text), 'function'
    s, e = statement.extend_statement(y, get, n)
    text = statement.join_lines(get, s, e)
    return s, e, statement.dedent_block(text), 'statement'


class TestExtendStatement(unittest.TestCase):
    def test_r_wrapped_call(self):
        src = 'rnorm(n = 1e2,\n      mean = 10,\n      sd = 2)\n'
        s, e, text = _span(src, 0)
        self.assertEqual((s, e), (0, 2))
        self.assertIn('sd = 2)', text)

    def test_r_unbraced_if(self):
        src = (
            'if (!requireNamespace("magrittr", quietly = TRUE))\n'
            '  install.packages("magrittr")\n'
            'library(magrittr)\n'
        )
        s, e, text = _span(src, 0)
        self.assertEqual(s, 0)
        self.assertEqual(e, 1)
        self.assertIn('install.packages', text)
        self.assertNotIn('library', text)

    def test_r_if_else(self):
        src = 'if (x > 0)\n  1\nelse\n  2\nnext <- 3\n'
        s, e, _text = _span(src, 0)
        self.assertEqual((s, e), (0, 3))

    def test_triple_quoted_string(self):
        src = 'text = """\nhello\n"""\npat = 1\n'
        s, e, text = _span(src, 0)
        self.assertEqual((s, e), (0, 2))
        self.assertIn('hello', text)
        self.assertTrue(text.rstrip().endswith('"""'))

    def test_caret_inside_triple_quoted_string(self):
        src = 'text = """\nhello\n"""\npat = 1\n'
        s, e, text = _span(src, 1)
        self.assertEqual((s, e), (0, 2))
        ast.parse(text)
        s2, e2, text2 = _span(src, 2)
        self.assertEqual((s2, e2), (0, 2))
        ast.parse(text2)


class TestDedent(unittest.TestCase):
    def test_method_becomes_module_def(self):
        src = '    def dist2(self):\n        return self.x\n'
        out = statement.dedent_block(src)
        ast.parse(out)
        self.assertTrue(out.startswith('def dist2'))


class TestPythonCompound(unittest.TestCase):
    def test_try_except_else_from_header(self):
        src = (
            'try:\n'
            '    import numpy as np\n'
            'except ImportError:\n'
            '    print("SKIP")\n'
            'else:\n'
            '    np.random.seed(17)\n'
            'done = 1\n'
        )
        s, e, text = _span(src, 0)
        self.assertEqual((s, e), (0, 5))
        ast.parse(text)
        self.assertNotIn('done', text)

    def test_except_walks_back_to_try(self):
        src = (
            'try:\n'
            '    import numpy as np\n'
            'except ImportError:\n'
            '    print("SKIP")\n'
        )
        s, e, text = _span(src, 2)
        self.assertEqual(s, 0)
        ast.parse(text)

    def test_inner_line_stays_one_statement(self):
        src = (
            'try:\n'
            '    import numpy as np\n'
            'except ImportError:\n'
            '    print("SKIP")\n'
        )
        _s, _e, text, mode = _send_at(src, 1)
        self.assertEqual(mode, 'statement')
        self.assertEqual(text.strip(), 'import numpy as np')
        ast.parse(text)

    def test_inner_print_does_not_steal_else(self):
        src = (
            'if cond:\n'
            '    print("SKIP")\n'
            'else:\n'
            '    x = 1\n'
        )
        _s, _e, text, mode = _send_at(src, 1)
        self.assertEqual(mode, 'statement')
        self.assertEqual(text.strip(), 'print("SKIP")')
        ast.parse(text)

    def test_decorator_plus_class(self):
        src = (
            '@dataclass\n'
            'class RunningMean:\n'
            '    n: int = 0\n'
            '    def update(self, x):\n'
            '        return x\n'
            'rm = RunningMean()\n'
        )
        s, e, text, mode = _send_at(src, 0)
        self.assertEqual(mode, 'function')
        self.assertEqual(s, 0)
        self.assertIn('@dataclass', text)
        self.assertIn('class RunningMean', text)
        self.assertNotIn('rm =', text)
        ast.parse(text)

    def test_for_try_from_for_header(self):
        src = (
            'total = 0\n'
            'for i in range(5):\n'
            '    try:\n'
            '        if i == 3:\n'
            '            raise ValueError("boom")\n'
            '        total += i\n'
            '    except ValueError as e:\n'
            '        print(e)\n'
            'print(total)\n'
        )
        s, e, text = _span(src, 1)
        self.assertEqual(s, 1)
        self.assertIn('except ValueError', text)
        ast.parse(text)


def _sample_root():
    env = os.environ.get('STATGHOST_SAMPLE')
    if env and os.path.isdir(env):
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    cand = os.path.abspath(os.path.join(here, '..', '..', '..', 'statghost', 'sample'))
    if os.path.isdir(os.path.join(cand, 'R')):
        return cand
    return None


def _is_cut(line):
    s = (line or '').strip()
    return s == '' or s.startswith('#')


def _collect_extracts(path):
    with open(path, encoding='utf-8') as f:
        rows = _lines(f.read())
    out = []
    seen = set()
    for y, line in enumerate(rows):
        if _is_cut(line):
            continue
        s, e, text, mode = _send_at('\n'.join(rows), y)
        key = (s, e, mode)
        if key in seen:
            continue
        seen.add(key)
        out.append((os.path.basename(path), y + 1, mode, text))
    return out


def _r_parse_batch(items):
    if not items:
        return []
    tmp = tempfile.mkdtemp(prefix='sgtf_')
    files = []
    for i, (_n, _y, _m, text) in enumerate(items):
        p = os.path.join(tmp, '%04d.R' % i)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(text or '')
        files.append(p)
    checker = os.path.join(tmp, 'check.R')
    with open(checker, 'w', encoding='utf-8') as f:
        f.write(
            'files <- commandArgs(TRUE)\n'
            'for (i in seq_along(files)) {\n'
            '  e <- tryCatch(parse(file = files[[i]], keep.source = TRUE),\n'
            '                error = function(err) err)\n'
            '  if (inherits(e, "error"))\n'
            '    cat(sprintf("FAIL\\t%d\\t%s\\n", i - 1L, conditionMessage(e)))\n'
            '}\n'
        )
    p = subprocess.run(
        ['Rscript', '--vanilla', checker] + files,
        capture_output=True, text=True, timeout=60,
    )
    fails = []
    for line in (p.stdout or '').splitlines():
        if not line.startswith('FAIL\t'):
            continue
        parts = line.split('\t', 2)
        if len(parts) >= 3:
            fails.append((items[int(parts[1])], parts[2]))
    return fails


class TestSampleExtracts(unittest.TestCase):
    """Automatic classroom gate: every unique Send extract must parse."""

    @classmethod
    def setUpClass(cls):
        cls.root = _sample_root()

    def test_r_samples_parse(self):
        if not self.root:
            self.skipTest('STATghost sample/ not found')
        items = []
        rdir = os.path.join(self.root, 'R')
        for name in sorted(os.listdir(rdir)):
            if name.endswith('.R'):
                items.extend(_collect_extracts(os.path.join(rdir, name)))
        self.assertGreater(len(items), 50)
        fails = _r_parse_batch(items)
        self.assertEqual(
            fails, [],
            '\n'.join(
                '%s L%s %s: %s' % (n, y, m, err)
                for (n, y, m, _t), err in fails
            ),
        )

    def test_python_samples_parse(self):
        if not self.root:
            self.skipTest('STATghost sample/ not found')
        fails = []
        pdir = os.path.join(self.root, 'Python')
        n = 0
        for name in sorted(os.listdir(pdir)):
            if not name.endswith('.py') or name == 'run_tests.py':
                continue
            for fname, y, mode, text in _collect_extracts(os.path.join(pdir, name)):
                n += 1
                try:
                    ast.parse(text or '')
                except SyntaxError as e:
                    fails.append('%s L%s %s: %s' % (fname, y, mode, e.msg))
        self.assertGreater(n, 50)
        self.assertEqual(fails, [], '\n'.join(fails))


if __name__ == '__main__':
    unittest.main(verbosity=2)
