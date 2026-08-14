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


if __name__ == '__main__':
    unittest.main(verbosity=2)
