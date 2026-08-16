# Thin statement bounds — vscode-R extendSelection / RStudio Ctrl+Enter idea.
# Brackets + trailing operators + unbraced R if/for/while/else body.
# One complete expression, not an IDE parser.
# Pure Python (no cudatext) so it can be checked against sample files.

from __future__ import annotations

import re
import textwrap

_END_OP = re.compile(
    r'(\(|,|\+|!|\$|\^|&|\*|-|=|:|~|\||/|\?|<|>|%[^%]*%)$'
)


def clean_line(text):
    """Drop trailing # comment outside quotes (vscode-R cleanLine)."""
    if not text:
        return ''
    out = []
    quote = None
    prev = ''
    for c in text:
        if c in '"\'`' :
            if quote is None:
                quote = c
            elif quote == c and prev != '\\':
                quote = None
        if c == '#' and quote is None:
            break
        out.append(c)
        prev = c
    return ''.join(out).rstrip()


def ends_in_operator(text):
    """True if this TEXT line continues the CODE line (comma, '(', %>% …).

    STATghost sniper: blank lines and `#` comments are chunk separators,
    not joiners (unlike vscode-R, which treats empty lines as continuations).
    """
    raw = (text or '').strip()
    if raw == '' or raw.startswith('#'):
        return False
    s = clean_line(text)
    if s.strip() == '':
        return False
    # Python suite headers (`try:`, `if x:`) are not R wrap operators.
    # Treating `:` as a joiner pulled inner body lines into the header
    # (and then _grow_py_compound swallowed the whole try/except).
    if _py_suite_kind(text) in ('owner', 'cont'):
        return False
    return _END_OP.search(s) is not None


def _newline_inside_string(text):
    quote = None
    prev = ''
    for c in text or '':
        if c in '"\'`' :
            if quote is None:
                quote = c
            elif quote == c and prev != '\\':
                quote = None
        if c == '\n' and quote is not None:
            return True
        prev = c
    return False


def _has_code_comment(text):
    """True if a `#` comment sits after code on this line (join would swallow)."""
    raw = text or ''
    cleaned = clean_line(raw)
    return len(cleaned) < len(raw.rstrip())


def _call_depth(text):
    """Net ( [ depth, ignoring quotes. `{` is a statement block, not a wrap.

    Used by collapse_wraps so `with(BOD, { plot(...); points(...) })`
    keeps newlines between statements (R needs them; joining would
    smash `) points` into one line and raise unexpected symbol).
    """
    depth = 0
    quote = None
    prev = ''
    for c in text or '':
        if quote:
            if c == quote and prev != '\\':
                quote = None
        elif c in '"\'`':
            quote = c
        elif c in '([':
            depth += 1
        elif c in ')]':
            depth -= 1
        prev = c
    return depth


def _is_call_continuer(text):
    """True if this line continues an open ( [ call, not a new statement.

    After `with(BOD, {` the call depth is still 1 (the `with(`), but
    `plot(...)` is a *new* statement inside `{`, not a wrap of `with(`.
    Continuers start with `)`, `]`, or `,` (lone closing / trailing
    argument of the *outer* call).
    """
    s = (text or '').lstrip()
    if not s:
        return False
    return s[0] in ')],'


def collapse_wraps(text):
    """Join editor wraps into one line (fig 1 → fig 2). Tokens unchanged.

    Joins while the previous line is an unfinished *call*: trailing
    operator (comma, `(`, `%>%`, …) **or** unmatched `(` / `[` depth
    *and* the next line continues that call (starts with `)` / `]` /
    `,`). `{` / `}` are statement braces — do not join `plot(...)`
    onto `with(BOD, {`, or `plot(...) points(...)` becomes a syntax
    error. Without call depth, a closing `)` alone on the next line
    stayed separate → STATghost still took the 2+ line
    `source(echo=TRUE)` path and the Config option looked dead.
    Leaves multi-line strings, `#` mid-line comments, blank sniper
    cuts, and unbraced `if` bodies.
    """
    if text is None or '\n' not in text:
        return text if text is not None else ''
    raw = text.replace('\r\n', '\n').replace('\r', '\n')
    if _newline_inside_string(raw):
        return text
    lines = raw.split('\n')
    out = [lines[0].rstrip()]
    for line in lines[1:]:
        prev = out[-1]
        nxt = line.strip()
        # Blank / whole-line `#` = sniper chunk cut (do not join across).
        if nxt == '' or nxt.startswith('#'):
            out.append(line)
            continue
        join = False
        if prev and not _has_code_comment(prev):
            if ends_in_operator(prev):
                join = True
            elif _call_depth(prev) > 0 and _is_call_continuer(nxt):
                join = True
        if join:
            out[-1] = prev + ' ' + nxt
            continue
        out.append(line.rstrip())
    return '\n'.join(out)


def _is_quote(c):
    return c in '"\'`'


def _is_open(c):
    return c in '([{'


def _is_close(c):
    return c in ')]}'


def _brackets_match(a, b):
    return {')': '(', ']': '[', '}': '{', '(': ')', '[': ']', '{': '}'}.get(a) == b


class _Pos:
    __slots__ = ('line', 'col')

    def __init__(self, line, col):
        self.line = line
        self.col = col


def _char_at(s, col):
    if col < 0 or col >= len(s):
        return ''
    return s[col]


def _next_char(p, looking_forward, get_line, ends_op, line_count):
    s = get_line(p.line)
    is_eof = False
    is_eol = False
    if looking_forward:
        if p.col != len(s):
            nxt = _Pos(p.line, p.col + 1)
        elif p.line < (line_count - 1):
            nxt = _Pos(p.line + 1, -1)
        else:
            is_eof = True
            nxt = _Pos(p.line, p.col)
        ns = get_line(nxt.line)
        if nxt.col == len(ns):
            if nxt.line == (line_count - 1) or not ends_op(nxt.line):
                is_eol = True
    else:
        if p.col != -1:
            nxt = _Pos(p.line, p.col - 1)
        elif p.line > 0:
            nxt = _Pos(p.line - 1, len(get_line(p.line - 1)) - 1)
        else:
            is_eof = True
            nxt = _Pos(p.line, p.col)
        if nxt.col == -1:
            if nxt.line <= 0 or not ends_op(nxt.line - 1):
                is_eol = True
    ch = _char_at(get_line(nxt.line), nxt.col)
    return ch, nxt, is_eol, is_eof


def _remainder_after_control_header(s):
    """Text after `if/for/while (...)` or `else`/`repeat`. None if not a header."""
    s = (s or '').strip()
    if not s:
        return None
    if re.match(r'^else\s+if\b', s, re.I):
        pass
    elif re.match(r'^(else|repeat)\b', s, re.I):
        m = re.match(r'^(?:else|repeat)\b(.*)$', s, re.I)
        return (m.group(1) if m else '').strip()
    m = re.match(r'^(?:else\s+)?(?:if|for|while)\b\s*', s, re.I)
    if not m:
        return None
    rest = s[m.end():]
    if not rest.startswith('('):
        return None
    depth = 0
    quote = ''
    prev = ''
    for i, c in enumerate(rest):
        if quote:
            if c == quote and prev != '\\':
                quote = ''
        elif c in '"\'`':
            quote = c
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return rest[i + 1:].strip()
        prev = c
    return None


def _joined_code(get_line, start, end):
    parts = []
    for i in range(start, end + 1):
        t = get_line(i)
        parts.append(clean_line(t if t is not None else ''))
    return ' '.join(parts).strip()


def _control_needs_body(get_line, start, end):
    rem = _remainder_after_control_header(_joined_code(get_line, start, end))
    return rem == ''


def _next_code_line(i, get_line, line_count):
    """Next code line after i. Skip `#` comments; stop on blank (sniper cut)."""
    j = i + 1
    while j < line_count:
        t = get_line(j)
        s = (t if t is not None else '').strip()
        if s == '':
            return None
        if s.startswith('#'):
            j += 1
            continue
        return j
    return None


def _grow_r_control(start, end, get_line, line_count, depth=0):
    """Attach unbraced if/for/while/repeat body and a following else.

    vscode-R stops at `if (cond)` because the parens match and the line
    does not end in an operator. R still needs the next expression.
    Blank lines stay sniper cuts (do not join across them).
    """
    if depth > 32:
        return start, end
    grown = True
    while grown:
        grown = False
        if _control_needs_body(get_line, start, end):
            nxt = _next_code_line(end, get_line, line_count)
            if nxt is not None:
                b0, b1 = _extend_brackets(nxt, get_line, line_count)
                b0, b1 = _grow_r_control(
                    b0, b1, get_line, line_count, depth + 1
                )
                if b1 > end:
                    end = b1
                    grown = True
                    continue
        nxt = _next_code_line(end, get_line, line_count)
        if nxt is None:
            break
        head = clean_line(get_line(nxt) or '').strip()
        if re.match(r'^else\b', head, re.I):
            # Only an R if/for/while/repeat span owns a following else.
            # A Python body line sitting above `else:` must stay one statement.
            head0 = clean_line(get_line(start) or '').strip()
            if not re.match(
                r'^(?:else\s+)?(?:if|for|while|repeat)\b', head0, re.I
            ):
                break
            e0, e1 = _extend_brackets(nxt, get_line, line_count)
            e0, e1 = _grow_r_control(e0, e1, get_line, line_count, depth + 1)
            if e1 > end:
                end = e1
                grown = True
    return start, end


def _extend_brackets(line, get_line, line_count):
    """Inclusive 0-based (start, end) via brackets + joining operators.

    Port of vscode-R `extendSelection`. On abort (unmatched), (line, line).
    """
    if line_count <= 0:
        return 0, 0
    if line < 0:
        line = 0
    if line >= line_count:
        line = line_count - 1

    def line_at(i):
        t = get_line(i)
        return t if t is not None else ''

    def ends_op(i):
        return ends_in_operator(line_at(i))

    looking_forward = True
    poss = {0: _Pos(line, 0), 1: _Pos(line, -1)}
    done = {0: False, 1: False}
    unmatched = {0: [], 1: []}
    abort = False
    quote = ''
    prev = ''
    while not abort and not (done[0] and done[1]):
        d = 1 if looking_forward else 0
        ch, nxt, is_eol, is_eof = _next_char(
            poss[d], looking_forward, line_at, ends_op, line_count
        )
        poss[d] = nxt
        if quote == '':
            if _is_quote(ch):
                quote = ch
            elif _is_open(ch) if looking_forward else _is_close(ch):
                unmatched[d].append(ch)
            elif _is_close(ch) if looking_forward else _is_open(ch):
                if not unmatched[d]:
                    looking_forward = not looking_forward
                    d2 = 1 if looking_forward else 0
                    unmatched[d2].append(ch)
                    done[d2] = False
                elif not _brackets_match(ch, unmatched[d].pop()):
                    abort = True
        else:
            if ch == quote:
                if looking_forward:
                    if prev != '\\':
                        quote = ''
                else:
                    nch, _, _, _ = _next_char(
                        poss[d], looking_forward, line_at, ends_op, line_count
                    )
                    if nch != '\\':
                        quote = ''
        if is_eol:
            if quote != '':
                # Multi-line string / """ — do not end the statement at EOL.
                if is_eof:
                    abort = True
            elif not unmatched[1 if looking_forward else 0]:
                done[1 if looking_forward else 0] = True
                looking_forward = not looking_forward
            elif is_eof:
                abort = True
        prev = ch
    if abort:
        return line, line
    return poss[0].line, poss[1].line


def _opener_if_inside_string(line, get_line):
    """If `line` sits inside a multi-line string, return the opener line.

    Sniper cut (blank / hash) bounds the scan. Caret on a line inside
    a triple-quoted assignment sends the whole assignment.
    """
    start = line
    while start > 0:
        s = (get_line(start - 1) or '').strip()
        if s == '' or s.startswith('#'):
            break
        start -= 1
    quote = ''
    opener = None
    for i in range(start, line):
        prev = ''
        for c in (get_line(i) or ''):
            if quote:
                if c == quote and prev != '\\':
                    quote = ''
                    opener = None
            elif c in '"\'`':
                quote = c
                opener = i
            prev = c
    if quote and opener is not None:
        return opener
    return line


def extend_statement(line, get_line, line_count):
    """Inclusive 0-based (start, end) of the complete expression at `line`.

    Brackets + trailing operators (vscode-R), then unbraced R `if`/`else`
    body (RStudio Ctrl+Enter), then Python suite / decorator growth.
    On abort (unmatched), returns (line, line).
    """
    line = _opener_if_inside_string(line, get_line)
    start, end = _extend_brackets(line, get_line, line_count)
    start, end = _grow_r_control(start, end, get_line, line_count)
    return _grow_py_compound(start, end, get_line, line_count)


# R: name <- function(  /  name = function(  /  `odd name` <- function(
_RE_R_FUN_HEAD = re.compile(
    r'^\s*(?:[.`\w]+|`[^`]+`)\s*(?:<-|=)\s*function\s*\('
)
# Python / Julia light (classroom multi-engine).
_RE_PY_DEF = re.compile(
    r'^(\s*)(?:async\s+)?(?:def|class)\s+[A-Za-z_]\w*\s*[(:]'
)
_RE_JL_FUN = re.compile(
    r'^\s*(?:function|macro)\s+[A-Za-z_!][\w!]*'
)
_RE_PY_OWNER = re.compile(
    r'^(?:async\s+)?(?:def|class|if|for|while|try|with|match)\b'
)
_RE_PY_CONTINUER = re.compile(
    r'^(?:elif|else|except|finally|case)\b'
)


def _py_suite_kind(line):
    """'owner' | 'cont' | 'deco' | None — Python compound / decorator line."""
    s = clean_line(line).strip()
    if not s:
        return None
    if s.startswith('@') and not s.startswith('@"') and not s.startswith("@'"):
        return 'deco'
    if not s.endswith(':'):
        return None
    if _RE_PY_OWNER.match(s):
        return 'owner'
    if _RE_PY_CONTINUER.match(s):
        return 'cont'
    return None


def _include_decorators(start, get_line):
    """Walk up adjacent @decorator lines (no blank between deco and def)."""
    i = start
    while i > 0:
        prev = get_line(i - 1)
        if _py_suite_kind(prev) == 'deco':
            i -= 1
            continue
        break
    return i


def _py_find_owner(line, get_line):
    """From elif/else/except/finally, walk up to if/try/for/while/with.

    Blank line is a sniper cut (STATghost Python REPL closes on blank).
    """
    my_ind = _indent_width(get_line(line))
    for j in range(line - 1, -1, -1):
        raw = get_line(j)
        s = (raw or '').strip()
        if s == '':
            return None
        if s.startswith('#'):
            continue
        ind = _indent_width(raw)
        if ind > my_ind:
            continue
        if ind < my_ind:
            return None
        kind = _py_suite_kind(raw)
        if kind == 'owner':
            return j
        if kind == 'cont':
            continue
        return None
    return None


def _py_extend_suite(start, get_line, line_count):
    """From first decorator or header, include body + same-indent continuers."""
    i = start
    while i < line_count and _py_suite_kind(get_line(i)) == 'deco':
        i += 1
    if i >= line_count:
        return start
    kind = _py_suite_kind(get_line(i))
    if kind not in ('owner', 'cont'):
        return (i - 1) if i > start else start
    head_ind = _indent_width(get_line(i))
    end = i
    j = i + 1
    while j < line_count:
        raw = get_line(j) or ''
        s = raw.strip()
        if s == '':
            return end
        if s.startswith('#'):
            j += 1
            continue
        ind = _indent_width(raw)
        nxt = _py_suite_kind(raw)
        if ind > head_ind:
            end = j
            j += 1
            continue
        if ind == head_ind and nxt == 'cont':
            end = j
            j += 1
            continue
        break
    return end


def _grow_py_compound(start, end, get_line, line_count):
    """Complete Python try/if/for/with/def/class and @decorator groups.

    Only grows when the *start* line is a header, continuer, or decorator.
    Inner body lines stay a single statement (then dedent_block on send).
    """
    kind = _py_suite_kind(get_line(start))
    if kind is None:
        return start, end
    i = start
    if kind == 'cont':
        owner = _py_find_owner(i, get_line)
        if owner is not None:
            i = owner
    i = _include_decorators(i, get_line)
    new_end = _py_extend_suite(i, get_line, line_count)
    if new_end < end:
        new_end = end
    return i, new_end


def dedent_block(text):
    """Strip common leading indent so a method / inner line is valid Python.

    R ignores indent; the Python REPL does not. Always safe for R.
    """
    if text is None:
        return ''
    raw = text.replace('\r\n', '\n').replace('\r', '\n')
    if raw.strip() == '':
        return raw
    out = textwrap.dedent(raw)
    lines = out.split('\n')
    indents = []
    for ln in lines:
        if ln.strip() == '':
            continue
        indents.append(len(ln) - len(ln.lstrip(' \t')))
    if not indents:
        return out
    m = min(indents)
    if m <= 0:
        return out
    return '\n'.join((ln[m:] if ln.strip() else ln) for ln in lines)


def _indent_width(line):
    s = line or ''
    n = 0
    for c in s:
        if c == ' ':
            n += 1
        elif c == '\t':
            n += 4
        else:
            break
    return n


def _is_blank_or_comment(line):
    s = (line or '').strip()
    return s == '' or s.startswith('#')


def enclosing_function(line, get_line, line_count):
    """Inclusive (start, end) of the function that contains `line`, or (None, None).

    RStudio / vscode-R idea: caret anywhere inside the body still sends the
    whole `name <- function(...) { ... }` (innermost when nested).
    Also light Python `def`/`class` (indent) and Julia `function`/`macro`.
    """
    if line is None or line_count is None or line_count <= 0:
        return None, None
    line = int(line)
    if line < 0:
        line = 0
    if line >= line_count:
        line = line_count - 1

    def line_at(i):
        t = get_line(i)
        return t if t is not None else ''

    # --- R: walk up; first head whose bracket extent covers caret = innermost
    for i in range(line, -1, -1):
        raw = line_at(i)
        if not _RE_R_FUN_HEAD.match(raw):
            continue
        s, e = extend_statement(i, get_line, line_count)
        if s <= line <= e:
            return s, e

    # --- Python: def/class at indent <= caret's code indent
    caret_raw = line_at(line)
    caret_ind = _indent_width(caret_raw)
    search_from = line
    if _py_suite_kind(caret_raw) == 'deco':
        j = line + 1
        while j < line_count and (
            _py_suite_kind(line_at(j)) == 'deco'
            or _is_blank_or_comment(line_at(j))
        ):
            j += 1
        if j < line_count and _RE_PY_DEF.match(line_at(j)):
            search_from = j
            caret_ind = _indent_width(line_at(j))
    if _is_blank_or_comment(caret_raw) and _py_suite_kind(caret_raw) != 'deco':
        # Use nearest code line below (or above) for indent reference.
        for j in range(line + 1, line_count):
            if not _is_blank_or_comment(line_at(j)):
                caret_ind = _indent_width(line_at(j))
                break
        else:
            for j in range(line - 1, -1, -1):
                if not _is_blank_or_comment(line_at(j)):
                    caret_ind = _indent_width(line_at(j))
                    break
    for i in range(search_from, -1, -1):
        raw = line_at(i)
        m = _RE_PY_DEF.match(raw)
        if not m:
            continue
        head_ind = _indent_width(raw)
        if head_ind > caret_ind:
            continue
        # Body continues while indent > head_ind. Blanks/comments inside
        # the block are included via the span i..end; trailing blanks after
        # the last body line are not (next dedent ends the def).
        end = i
        for j in range(i + 1, line_count):
            lj = line_at(j)
            if _is_blank_or_comment(lj):
                continue
            if _indent_width(lj) > head_ind:
                end = j
                continue
            break
        deco = _include_decorators(i, line_at)
        if deco <= line <= end:
            return deco, end
    # --- Julia: function/macro … end (bracket-free; match end at col)
    for i in range(line, -1, -1):
        raw = line_at(i)
        if not _RE_JL_FUN.match(raw):
            continue
        depth = 1
        end = i
        for j in range(i + 1, line_count):
            lj = line_at(j).strip()
            if re.match(r'^(?:function|macro|struct|mutable\s+struct|for|while|if|let|quote|begin)\b', lj):
                depth += 1
            if re.match(r'^end\b', lj):
                depth -= 1
                if depth == 0:
                    end = j
                    break
            end = j
        if i <= line <= end and depth == 0:
            return i, end

    return None, None


def join_lines(get_line, start, end):
    parts = []
    for i in range(start, end + 1):
        t = get_line(i)
        parts.append(t if t is not None else '')
    return '\n'.join(parts)
