# EB-0 clipboard contract with STATghost (twin: src/ubridgecmd.pas).
# UTF-8 on the system clipboard. First line:
#   #. STATGHOST:<CMD> <nonce>
# CMD EVAL | EVAL_KEEP | ARM | IDLE | QUIT | CLEAR …
# EVAL_KEEP is EVAL plus restore the editor (plugin keep_focus).
# Note1-shaped so a leak into R/Python/Julia is a comment.
# <nonce> makes every plugin send unique — same student code / same toggle
# must re-fire (pseudo-random reruns; Arm/Idle more than once). Without it
# the clipboard text would match FLastClip and STATghost would skip, and
# the token sitting on the clipboard would otherwise toggle every 250 ms.
# Pure Python (no cudatext).

from __future__ import annotations

import itertools
import time

PREFIX = '#. STATGHOST:'

CMD_TOGGLE_ARM = 'TOGGLE_ARM'
CMD_ARM = 'ARM'
CMD_IDLE = 'IDLE'
CMD_EVAL = 'EVAL'
CMD_EVAL_KEEP = 'EVAL_KEEP'
CMD_QUIT = 'QUIT'
CMD_CLEAR = 'CLEAR'


_counter = itertools.count()


def _nonce():
    return '%s-%s' % (time.time_ns(), next(_counter))


def next_arm_cmd(plugin_shows_armed):
    """Absolute ARM/IDLE — never TOGGLE. A guessed flip inverts SG."""
    return CMD_IDLE if plugin_shows_armed else CMD_ARM


def make_command(name):
    cmd = (name or '').strip().upper()
    return PREFIX + cmd + ' ' + _nonce()


def make_eval(code, keep_focus=False):
    """Wrap student code so a repeat send is a new clipboard payload.

    keep_focus: EVAL_KEEP — STATghost restores the editor after this eval
    without changing Settings → Focus after eval.
    """
    cmd = CMD_EVAL_KEEP if keep_focus else CMD_EVAL
    return make_command(cmd) + '\n' + (code if code is not None else '')


def parse_message(text):
    """Return (cmd, body) or (None, None).

    First line `#. STATGHOST:<CMD> [nonce]`; body is the rest (EVAL).
    """
    raw = text if text is not None else ''
    if raw.startswith('\ufeff'):
        raw = raw[1:]
    nl = raw.find('\n')
    if nl < 0:
        head, body = raw, ''
    else:
        head, body = raw[:nl], raw[nl + 1:]
    if head.endswith('\r'):
        head = head[:-1]
    head = head.strip()
    if not head.startswith(PREFIX):
        return None, None
    tail = head[len(PREFIX):].strip()
    if not tail:
        return None, None
    sp = tail.find(' ')
    if sp < 0:
        cmd = tail.upper()
    else:
        cmd = tail[:sp].upper()
    if not cmd:
        return None, None
    return cmd, body
