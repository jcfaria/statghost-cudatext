#!/usr/bin/env python3
# Automated unit checks for cuda_statghost (no CudaText host required).
# Run: python3 test_unit.py

from __future__ import annotations

import os
import sys
import unittest

# Allow `python3 test_unit.py` from this folder or repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import paths  # noqa: E402
import protocol  # noqa: E402
import statement  # noqa: E402


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


if __name__ == '__main__':
    unittest.main(verbosity=2)
