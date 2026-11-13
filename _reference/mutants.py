# SPOILERS. Proves the week 1 to 9 suites have teeth: each mutant plants one plausible student bug in the
# reference compiler, and the suite must catch (kill) every one. A few minutes for all of them.
#   python _reference/mutants.py               every mutant, stopping at the first test that catches it
#   python _reference/mutants.py w6 grad       only mutants whose names contain 'w6' or 'grad'
#   python _reference/mutants.py --matrix      every mutant against every test (which tests catch what)
#   python _reference/mutants.py --checks      also switch off each validation and each simplifier rule, one at a time
import os, re, sys, json, glob, threading, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SRC = open(os.path.join(HERE, 'uirc.py'), encoding='utf-8').read()
WEEKS = (1, 2, 3, 4, 5, 6, 7, 8, 9)

# (name, [(old, new), ...]) -- every old must occur exactly once in uirc.py
M = [
  # interpreter: i32
  ("add doesn't wrap",            [("  if op == 'add': return wrap(a + b)", "  if op == 'add': return a + b")]),
  ("mul doesn't wrap",            [("  if op == 'mul': return wrap(a * b)", "  if op == 'mul': return a * b")]),
  ("div floors like Python",      [("  q = wrap(tdiv(a, b))", "  q = wrap(a // b)")]),
  ("mod uses Python %",           [("return q if op == 'div' else wrap(a - q * b)", "return q if op == 'div' else wrap(a % b)")]),
  ("div by zero returns 0",       [('  if b == 0: raise UIRError(f"{op} by zero")', "  if b == 0: return 0")]),
  ("shl allows 32",               [("if not 0 <= b <= 31", "if not 0 <= b <= 32")]),
  ("shl doesn't wrap",            [("    return wrap(a << b)", "    return a << b")]),
  ("xor bool is equality",        [("return a != b if dt == 'bool'", "return a == b if dt == 'bool'")]),
  ("cmplt is <=",                 [("if op == 'cmplt': return a < b", "if op == 'cmplt': return a <= b")]),
  ("where branches swapped",      [("return vs[1] if vs[0] else vs[2]", "return vs[2] if vs[0] else vs[1]")]),
  # interpreter: f32
  ("f32 ops not rounded",         [("return math.nan if math.isnan(r) else f32(r)", "return r")]),
  ("max ignores NaN",             [("if dt == 'f32' and (math.isnan(a) or math.isnan(b)): return math.nan", "if False: return math.nan")]),
  ("recip 0 ignores sign",        [("math.copysign(math.inf, a) if a == 0", "math.inf if a == 0")]),
  ("f32 consts not rounded",      [("f32(float(v)) if dtype == 'f32' else v", "float(v) if dtype == 'f32' else v")]),
  # interpreter: cast
  ("f32->i32 rounds",             [("  return math.trunc(v)\n", "  return round(v)\n")]),
  ("f32->i32 no range check",     [("if math.isnan(v) or math.isinf(v) or not (INT_MIN <= math.trunc(v) <= INT_MAX)", "if math.isnan(v) or math.isinf(v)")]),
  ("bool->num always 1",          [("return int(v) if to == 'i32' else float(v)", "return 1 if to == 'i32' else 1.0")]),
  ("i32->f32 not rounded",        [("  if to == 'f32': return f32(float(v))", "  if to == 'f32': return float(v)")]),
  # interpreter: equality, order, laziness
  ("NaN != NaN in assert",        [("return isinstance(b, float) and math.isnan(b)", "return False")]),
  ("-0.0 != 0.0 in assert",       [("  return a == b\n\n# ----", "  return a == b and str(a) == str(b)\n\n# ----")]),
  ("asserts in reverse order",    [("  for n in order:\n    u = names[n]", "  for n in reversed(order):\n    u = names[n]")]),
  ("index allows negative",       [("    if not 0 <= j < len(x): raise UIRError(f\"index {j} out of range\")", "    if not j < len(x): raise UIRError(f\"index {j} out of range\")")]),
  ("evaluates everything",        [("    if u.op == 'assert' and not assert_value(u, names)", "    if u.op != 'assert' and u.op != 'param' and not isinstance(evaluate(u, None), bool): pass\n    if u.op == 'assert' and not assert_value(u, names)")]),
  ("no memoization",              [("def evaluate(root, env):", "def evaluate(root, env):\n  if root.src and root.op != 'call': [evaluate(s, env) for s in root.src]")]),
  # interpreter: call / param
  ("global memo across calls",    [("  memo = {}\n  for u in toposort(root):", "  memo = GLOBAL\n  for u in toposort(root):\n    if id(u) in memo and u.op not in ('const',): continue"),
                                   ("def evaluate(root, env):", "GLOBAL = {}\ndef evaluate(root, env):")]),
  ("nested body sees outer env",  [("elif u.op == 'call': r = evaluate(u.src[0], dict(enumerate(v)))", "elif u.op == 'call': r = evaluate(u.src[0], env if env else dict(enumerate(v)))")]),
  ("param outside call is 0",     [("if env is None or u.arg not in env: raise", "if env is None: r = 0\n      elif u.arg not in env: raise"),
                                   ("      r = env[u.arg]", "      else: r = env[u.arg]")]),
  ("missing args not checked",    [('need(slot < len(args), f"no arg for param {slot}")', "pass")]),
  ("arg types not checked",       [('need((args[slot].dtype, args[slot].shape) == (p.dtype, p.shape), f"arg {slot} type mismatch")', "need(slot < len(args), '')")]),
  ("param slot types unchecked",  [('if u.arg in ps and (ps[u.arg].dtype, ps[u.arg].shape) != (u.dtype, u.shape): raise UIRError(f"param {u.arg} used with two types")', "pass")]),
  # parser / types
  ("implicit dtype mixing",       [('need(n == 2 and src[0].dtype == src[1].dtype, "two operands of the same dtype")', 'need(n == 2, "two operands")')]),
  ("int literals unbounded",      [("if not INT_MIN <= int(t) <= INT_MAX: raise", "if False: raise")]),
  ("redefinition allowed",        [('if name in names: raise UIRError(f"%{name} defined twice")', "pass")]),
  ("stack dtypes unchecked",      [('need(len({s.dtype for s in src}) == 1, "dtype mismatch")', "pass")]),
  ("void operands allowed",      [("need(s.dtype != 'void' or (op in ('after', 'end') and s.op in EFFECT), \"void operand\")", "need(True, \"void operand\")")]),
  ("implicit broadcast allowed",  [('need(len({x.shape for x in src}) == 1, "ALU operands must share one shape (no implicit broadcast: use expand)")', "pass")]),
  # grammar and static checks (added after the audit)
  ("unknown attributes ignored",  [("if k not in ATTRS.get(op, set()): raise UIRError", "if False: raise UIRError")]),
  ("duplicate attributes allowed",[("if k in attrs: raise UIRError(f\"attribute {k} given twice\")", "pass")]),
  ("attributes before operands",  [('elif attrs: raise UIRError("operands come before attributes")', "elif False: pass")]),
  ("loose float literals",        [("  if FLOAT_RE.fullmatch(t): return const(float(t), 'f32')", "  try: return const(float(t), 'f32')\n  except ValueError: pass")]),
  ("slot types checked on call only", [("      free_params(u)          # one slot used with two types", "      # free_params(u)          # one slot used with two types")]),
  ("max(-0.0, 0.0) order-dependent", [("    if a == b == 0 and dt == 'f32': return a if math.copysign(1, a) > 0 else b   # max(-0.0, 0.0) is +0.0 either way\n", "")]),
  ("x + 0.0 -> x on f32",         [("y.arg == 0 and math.copysign(1, y.arg) < 0: return x", "y.arg == 0: return x")]),
  # week 4: rank-1 values, reduce, expand, stage, rangeify
  ("w4 fold right to left",       [("  acc = xs[0]\n  for x in xs[1:]: acc = alu(op, [dt, dt], [acc, x], dt)", "  acc = xs[-1]\n  for x in xs[-2::-1]: acc = alu(op, [dt, dt], [acc, x], dt)")]),
  ("w4 fold from zero",           [("  acc = xs[0]\n  for x in xs[1:]: acc = alu(op, [dt, dt], [acc, x], dt)", "  acc = ZERO[dt]\n  for x in xs: acc = alu(op, [dt, dt], [acc, x], dt)")]),
  ("w4 fold skips nan",           [("  for x in xs[1:]: acc = alu(op, [dt, dt], [acc, x], dt)", "  for x in xs[1:]: acc = acc if isinstance(x, float) and math.isnan(x) else alu(op, [dt, dt], [acc, x], dt)")]),
  ("w4 reduce op ignored",        [("lambda r: fold(op, u.dtype, [at(x, l + r) for l in lead])", "lambda r: fold('add', u.dtype, [at(x, l + r) for l in lead])")]),
  ("w4 expand scalar is zero",    [("lambda i: x if not xs else at(x, tuple(0 if a == 1 else j", "lambda i: ZERO[u.dtype] if not xs else at(x, tuple(0 if a == 1 else j")]),
  ("w4 stage zeroes",             [("  if u.op == 'stage': return x\n", "  if u.op == 'stage': return tabulate(u.shape, lambda i: ZERO[u.dtype]) if u.shape else x\n")]),
  ("w4 elementwise uses x[0]",    [("[alu(u.op, dts, [f[i] for f in fl], u.dtype) for i in range(prod(u.shape))]", "[alu(u.op, dts, [f[0] for f in fl], u.dtype) for i in range(prod(u.shape))]")]),
  ("w4 shaped on open range ok",  [("  if op in SHAPE_OPS: need(not any(opens(x) for x in src[:1]), \"shaped values can't depend on an open range\")\n", "")]),
  ("w4 reduce takes scalars",     [("need(len(src) == 1 and 1 <= m <= len(src[0].shape),", "need(len(src) == 1 and m >= 1,")]),
  ("w4 reduce on bool",           [('need(src[0].dtype in NUM, "reduce works on i32 or f32")', 'pass')]),
  ("w5 expand grows non-1 axes",  [("need(fr == () or (len(fr) == len(to) and all(a == b or a == 1 for a, b in zip(fr, to))),", "need(fr == () or len(fr) == len(to),")]),
  ("w4 render skips rangeify",    [("u.op in ('range', 'mma') or u.op in SHAPE_OPS or (u.op in ALU and u.shape) or len(u.shape) >= 2", "u.op in ('range', 'mma')"), (" or (len(u.shape) == 1 and u.shape[0] > 32 and u.op not in MEM) for u in all_nodes(names))", " for u in all_nodes(names))")]),
  ("w4 render reduce reversed",   [("el(x, (c(0),) * m + idx)))  # start from the first element", "el(x, unflat(c(T - 1), lead) + idx)))"),
                                   ("el(x, unflat(A('add', r, c(1)), lead) + idx)", "el(x, unflat(A('add', A('mul', r, c(-1)), c(T - 2)), lead) + idx)")]),
  ("w4 render reduce from zero",  [("acc1 = after(acc, store(sv(acc, c(0)), el(x, (c(0),) * m + idx)))  # start from the first element", "acc1 = after(acc, store(sv(acc, c(0)), const(0, u.dtype)))"),
                                   ('r = rng(T - 1, f"red{t}")', 'r = rng(T, f"red{t}")'),
                                   ("el(x, unflat(A('add', r, c(1)), lead) + idx)", "el(x, unflat(r, lead) + idx)")]),
  ("w4 render expand zero",       [("    elif op == 'expand': out = low(u.src[0]) if not xs else", "    elif op == 'expand': out = (const(False, 'bool') if u.dtype == 'bool' else const(0, u.dtype)) if not xs else")]),
  ("w4 render elementwise at 0",  [("    if op in ALU: out = UOp(op, tuple(el(x, idx) for x in u.src), None, u.dtype, ())", "    if op in ALU: out = UOp(op, tuple(el(x, tuple(c(0) for _ in idx)) for x in u.src), None, u.dtype, ())")]),
  ("w4 render store loop short",  [('view, val = u.src; r = rng(val.shape[0], f"st{id(u)}")', 'view, val = u.src; r = rng(val.shape[0] - 1, f"st{id(u)}")')]),
  ("w4 render stage reads x[0]",  [("      out = load(sv(filled, flat_of(idx, u.shape)), u.dtype)", "      out = load(sv(filled, c(0)), u.dtype)")]),
  ("w4 render load at offset 0",  [("    elif op == 'load': out = load(sv(low(u.src[0]), idx[0]), u.dtype)", "    elif op == 'load': out = load(sv(low(u.src[0]), c(0)), u.dtype)")]),
  ("w4 no size threshold",        [(" or (len(u.shape) == 1 and u.shape[0] > 32 and u.op not in MEM) for u in all_nodes(names))", " for u in all_nodes(names))")]),
  # simplifier
  ("x*0 -> 0 on f32",             [("  if op == 'max' and x is y: return x", "  if op == 'mul' and isc(y) and y.arg == 0: return y\n  if op == 'max' and x is y: return x")]),
  ("(x*c)/c ignores wrap",        [(" and bounds(x, bm) != (INT_MIN, INT_MAX):", ":")]),
  ("i32 rules applied to f32",    [("  if dt == 'i32' or (op == 'xor' and dt == 'bool'):", "  if dt in ('i32', 'f32') or (op == 'xor' and dt == 'bool'):")]),
  ("mod bounds ignore sign",      [("r = (0, min(m - 1, a1)) if a0 >= 0 else (-(m - 1), m - 1)", "r = (0, m - 1)")]),
  ("bounds clamp instead of wrap",[("if c is not None and INT_MIN <= min(c) and max(c) <= INT_MAX: r = (min(c), max(c))", "if c is not None: r = (max(min(c), INT_MIN), min(max(c), INT_MAX))")]),
  ("no const-right canonicalize", [("if op in COMM and isc(s[0]) and not isc(s[1])", "if False")]),
  ("cmplt bounds off by one",     [("      if a1 < b0: return const(True, 'bool')", "      if a1 <= b0: return const(True, 'bool')")]),
  ("div elim off by one",         [("if op == 'div' and a0 >= 0 and b0 > 0 and a1 < b0", "if op == 'div' and a0 >= 0 and b0 > 0 and a1 <= b0")]),
  # bottom-up inlining never meets a nested call, so this bug needs top-down inlining to show up
  ("top-down inline enters bodies",[("new[id(u)] = UOp('call', (u.src[0],) + tuple", "new[id(u)] = UOp('call', (substitute(u.src[0], args),) + tuple"),
                                   ("def simplify(root):\n", "def simplify(root):\n  if root.op == 'call': root = substitute(root.src[0], root.src[1:])\n")]),
  ("no call inlining",            [("  if op == 'call': return substitute(s[0], s[1:])\n", "")]),
  ("no hash consing",             [("      if (u := UOp._cache.get(key)) is not None: return u\n", "")]),
  # ---------------- week 2: memory semantics ----------------
  ("w2 shrink offsets don't add", [("    sid, off = view(v.src[0]); return sid, off + val(v.src[1])", "    sid, off = view(v.src[0]); return sid, val(v.src[1])")]),
  ("w2 load ignores the offset",  [("vals[id(u)] = tuple(mem[sid][off:off + u.shape[0]]) if u.shape else mem[sid][off]; continue", "vals[id(u)] = tuple(mem[sid][0:u.shape[0]]) if u.shape else mem[sid][0]; continue")]),
  ("w2 rank-1 store writes one",  [("        if u.src[0].shape: mem[sid][off:off + len(x)] = list(x)", "        if u.src[0].shape: mem[sid][off] = x[0]")]),
  ("w2 alloc not zeroed",         [("      if op == 'alloc': mem[id(u)] = [ZERO[u.dtype]] * u.arg[1]; continue", "      if op == 'alloc': mem[id(u)] = [ZERO[u.dtype] + 1] * u.arg[1]; continue")]),
  ("w2 identical buffers merge",  [("('buffer', int(attrs['slot']), n, data, name)", "('buffer', int(attrs['slot']), n, data, '')")]),
  ("w2 allocs share storage",     [("UOp('alloc', (), ('alloc', n, name), dt, (n,))", "UOp('alloc', (), ('alloc', n, ''), dt, (n,))")]),
  ("w2 final version not followed", [("      while id(v) in nxt: v = nxt[id(v)]", "      pass")]),
  # ---------------- week 2: static checks ----------------
  ("w2 bounds unchecked",         [("    need(lo >= 0 and hi + k <= plen, f\"can't prove", "    need(True, f\"can't prove")]),
  ("w2 bounds allow negative",    [("    need(lo >= 0 and hi + k <= plen, f\"can't prove", "    need(hi + k <= plen, f\"can't prove")]),
  ("w2 bounds off by one",        [("    need(lo >= 0 and hi + k <= plen, f\"can't prove", "    need(lo >= 0 and hi + k <= plen + 1, f\"can't prove")]),
  ("w2 nested view vs storage",   [("k, plen = (shape[0] if shape else 1), (src[0].shape[0] if src[0].shape else 1)", "k, plen = (shape[0] if shape else 1), storage_of(src[0]).shape[0]")]),
  ("w2 two stores per version",   [("    if len(ss) > 1: raise UIRError", "    if False: raise UIRError")]),
  ("w2 unsequenced store ok",     [("    if u.op in ('store', 'mma') and id(u) not in sequenced: raise", "    if False: raise")]),
  ("w2 duplicate slots ok",       [("  if len(slots) != len(set(slots)): raise", "  if False: raise")]),
  ("w2 after version unchecked",  [("if src[1].op in ('store', 'mma'): need(version_of(src[1].src[0]) is src[0], ", "if src[1].op in ('store', 'mma'): need(True, ")]),
  ("w2 memory in call body ok",   [("    need(not any(u.op in MEM or u.op in ('load', 'store') for u in toposort(body, into_bodies=True)), ", "    need(True, ")]),
  ("w2 memory as ALU operand ok", [("  if op not in ('shrink', 'load', 'store', 'after', 'mma'): need(not any(is_mem(s) for s in src), ", "  if False: need(True, ")]),
  ("w2 store type unchecked",     [("    need((src[0].dtype, src[0].shape) == (src[1].dtype, src[1].shape), ", "    need(True, ")]),
  ("w2 data length unchecked",    [("            if len(toks) != n: raise", "            if False: raise")]),
  ("w2 data dtype unchecked",     [("              if c is None or c.dtype != dt: raise", "              if c is None: raise")]),
  ("w2 no ordering cycle check",  [("      if st == 1: raise UIRError(\"a load of an old", "      if False: raise UIRError(\"a load of an old")]),
  # ---------------- week 2: renderer ----------------
  ("w2 loads not before stores",  [("    if n.op in ('store', 'mma'): d += [", "    if False: d += [")]),
  ("w2 C plain signed add",       [("      e = f\"(int32_t)((uint32_t){a[0]} {dict(add='+', mul='*', shl='<<')[op]} (uint32_t){a[1]})\"",
                                    "      e = f\"({a[0]} {dict(add='+', mul='*', shl='<<')[op]} {a[1]})\"")]),
  ("w2 C div without -1 guard",   [("    elif op == 'div': e = f\"({a[1]} == -1 ? (int32_t)(0u - (uint32_t){a[0]}) : {a[0]} / {a[1]})\"", "    elif op == 'div': e = f\"({a[0]} / {a[1]})\"")]),
  ("w2 C mod without -1 guard",   [("    elif op == 'mod': e = f\"({a[1]} == -1 ? 0 : {a[0]} % {a[1]})\"", "    elif op == 'mod': e = f\"({a[0]} % {a[1]})\"")]),
  ("w2 C max ignores nan",        [("  if (isnan(a) || isnan(b)) return NAN;\n", "")]),
  ("w2 C max ignores -0.0",       [("  if (a == 0.0f && b == 0.0f) return signbit(a) ? b : a;", "")]),
  ("w2 C cast to i32 rounds",     [("else f\"(({t}){a[0]})\"", "else f\"(({t})lrintf({a[0]}))\"")]),
  ("w2 C float literals 6 digits",[("  return float.hex(v) + 'f'", "  return ('%.6g' % v) + ('' if any(ch in '%.6g' % v for ch in '.en') else '.0') + 'f'")]),
  ("w2 C alloc not zeroed",       [("    return f\"{pad}{CT[u.dtype]} a{i}[{u.arg[1]}] = {{0}};\"", "    return f\"{pad}{CT[u.dtype]} a{i}[{u.arg[1]}] = {{1}};\"")]),
  ("w2 C rank-1 store one elem",  [("        if u.src[0].shape: lines.extend(f\"{pad}{p}[{o} + {j}] = {x}[{j}];\" for j in range(u.src[0].shape[0]))",
                                    "        if u.src[0].shape: lines.append(f\"{pad}{p}[{o}] = {x}[0];\")")]),
  ("w2 C rank-1 load no offset",  [("', '.join(f\"{p}[{o} + {j}]\" for j in range(u.shape[0]))", "', '.join(f\"{p}[{j}]\" for j in range(u.shape[0]))")]),
  ("w2 C nested offsets lost",    [("    return p, (off if o == '0' else f\"{o} + {off}\")", "    return p, off")]),
  ("w2 C where swapped",          [("    elif op == 'where': e = f\"({a[0]} ? {a[1]} : {a[2]})\"", "    elif op == 'where': e = f\"({a[0]} ? {a[2]} : {a[1]})\"")]),
  ("w2 C cmplt as <=",            [("    elif op == 'cmplt': e = f\"({a[0]} < {a[1]})\"", "    elif op == 'cmplt': e = f\"({a[0]} <= {a[1]})\"")]),
  # ---------------- week 3: loops ----------------
  ("w3 loads never move into loops",      [("      paths[id(n)] = P\n", "      pass\n")]),
  ("w3 loads follow their deepest use",   [("base, P = paths[id(n)], common([paths[id(c)] for c in cons[id(n)]])", "base, P = paths[id(n)], max([paths[id(c)] for c in cons[id(n)]], key=len)")]),
  ("w3 placement sees only the roots",    [("  for r in universe: allnodes += toposort(r, seen=aseen)", "  for r in (): allnodes += toposort(r, seen=aseen)")]),
  ("w3 loop runs one extra time",         [("for t in range(val(r.src[0])):", "for t in range(val(r.src[0]) + 1):")]),
  ("w3 zero-trip loops run once",         [("for t in range(val(r.src[0])):", "for t in range(max(val(r.src[0]), 1)):")]),
  ("w3 loop runs backwards",              [("for t in range(val(r.src[0])):", "for t in reversed(range(val(r.src[0]))):")]),
  ("w3 render loop uses <=",              [("{rv} < {ex(r.src[0])}; {rv}++", "{rv} <= {ex(r.src[0])}; {rv}++")]),
  ("w3 render loop starts at 1",          [("for (int32_t {rv} = 0;", "for (int32_t {rv} = 1;")]),
  ("w3 end doesn't close its range",      [("    elif x.op == 'end': o = o - {x.src[-1]}", "    elif x.op == 'end': o = o")]),
  ("w3 bounds may depend on ranges",      [("    need(not opens(src[0]), \"a range's bound can't depend on another range\")\n", "")]),
  ("w3 end need not use its range",       [("    need(any(src[-1] in opens(x) for x in src[:-1]), \"end closes a range its effects don't use\")\n", "")]),
  ("w3 asserts may read open ranges",     [("  if op in ('assert', 'call'): need(", "  if op in ('call',): need(")]),
  ("w3 calls may take open-range args",   [("  if op in ('assert', 'call'): need(", "  if op in ('assert',): need(")]),
  ("w3 a range may close twice",          [("      if closed.setdefault(id(r), u) is not u: raise UIRError(\"a range can be closed by only one end\")", "      closed.setdefault(id(r), u)")]),
  ("w3 unclosed loops allowed",           [("        if id(r) not in closed: raise UIRError(f\"range %{r.arg[1]} is never closed by an end\")", "        pass")]),
  ("w3 in-loop afters are outputs",       [("    if u.op == 'after' and not opens(u): nxt[id(u.src[0])] = u", "    if u.op == 'after': nxt[id(u.src[0])] = u")]),
  ("w3 range interval one too tight",     [("  elif u.op == 'range': r = (0, max(b(u.src[0])[1] - 1, 0))", "  elif u.op == 'range': r = (0, max(b(u.src[0])[1] - 2, 0))")]),
  ("w3 range interval is [0, 0]",         [("  elif u.op == 'range': r = (0, max(b(u.src[0])[1] - 1, 0))", "  elif u.op == 'range': r = (0, 0)")]),
  ("w3 values hoisted to outer loops",    [("    deepest = max(o, key=lambda q: len(chain(q)))", "    deepest = min(o, key=lambda q: len(chain(q)))")]),
  ("w3 after-on-loop skips memory check", [("      need(any(storage_of(st.src[0]) is storage_of(src[0]) for st in sts), \"the loop must store into the memory after names\")", "      pass")]),
  ("w3 after-on-loop accepts a stale version", [("      need(all(entry(st.src[0]) is src[0] for st in sts if storage_of(st.src[0]) is storage_of(src[0])),", "      need(True or all(entry(st.src[0]) is src[0] for st in sts if storage_of(st.src[0]) is storage_of(src[0])),")]),
  ("w3 end accepts values",               [("    need(all(x.op in EFFECT for x in src[:-1]), \"end repeats effects: stores or ends\")", "    pass")]),
  ("w3 stores under ends unsequenced",    [("    if u.op == 'after': sequenced.update(id(st) for st in stores_under(u.src[1]))", "    if u.op == 'after': sequenced.update([id(u.src[1])])")]),
  ("w3 nesting demands every range",      [("    if not set(outer) <= set(c[:-1]):", "    if set(outer) != set(c[:-1]):")]),
  # ---------------- week 5: movement ops ----------------
  # interpreter semantics (caught by run tests with independently computed values)
  ("w5 reshape column-major",     [("  if u.op == 'reshape': return nest(nflat(x), u.shape)", "  if u.op == 'reshape': return tabulate(u.shape, lambda i: nflat(x)[sum(a * prod(u.shape[:k]) for k, a in enumerate(i))])")]),
  ("w5 permute inverse",          [("      for k, p in enumerate(u.arg): s_[p] = i[k]", "      for k, p in enumerate(u.arg): s_[k] = i[p]")]),
  ("w5 pad sides swapped",        [("      j = tuple(a - pads[2 * k] for k, a in enumerate(i))", "      j = tuple(a - pads[2 * k + 1] for k, a in enumerate(i))")]),
  ("w5 pad fill not zero",        [("      return at(x, j) if all(0 <= a < d for a, d in zip(j, xs)) else ZERO[u.dtype]", "      return at(x, j) if all(0 <= a < d for a, d in zip(j, xs)) else (1.0 if u.dtype == 'f32' else 1)")]),
  ("w5 shrink offset sign",       [("lambda i: at(x, tuple(a + o for a, o in zip(i, v[1:]))))", "lambda i: at(x, tuple(a - o for a, o in zip(i, v[1:]))))")]),
  ("w5 expand reads i not 0",     [("at(x, tuple(0 if a == 1 else j for a, j in zip(xs, i))))", "at(x, tuple(j for a, j in zip(xs, i))))")]),
  ("w5 reduce pops trailing axes",[("[at(x, l + r) for l in lead]", "[at(x, r + l) for l in lead]")]),
  ("w5 reduce folds column-major",[("    op, m = u.arg; lead = list(itertools.product(*[range(d) for d in xs[:m]]))", "    op, m = u.arg; lead = [t[::-1] for t in itertools.product(*[range(d) for d in reversed(xs[:m])])]")]),
  # renderer (caught by render tests: compiled C vs the interpreter)
  ("w5 render pad mask off by one", [("A('cmplt', i, c(l + d), dt='bool')", "A('cmplt', i, c(l + d + 1), dt='bool')")]),
  ("w5 render shrink offset sign", [("    elif op == 'vshrink': out = el(u.src[0], tuple(add(low(o), i) for i, o in zip(idx, u.src[1:])))", "    elif op == 'vshrink': out = el(u.src[0], tuple(A('add', i, A('mul', low(o), c(-1))) for i, o in zip(idx, u.src[1:])))")]),
  ("w5 render expand reads i",    [("tuple(c(0) if a == 1 and b != 1 else i for a, b, i in zip(xs, u.shape, idx))", "tuple(i for a, b, i in zip(xs, u.shape, idx))")]),
  ("w5 render reduce column-major", [("el(x, unflat(A('add', r, c(1)), lead) + idx)", "el(x, unflat(A('add', r, c(1)), lead[::-1])[::-1] + idx)")]),
  ("w5 render stack chain off by one", [("A('cmplt', idx[0], c(j + 1), dt='bool')", "A('cmplt', idx[0], c(j), dt='bool')")]),
  ("w5 render index pops the end", [("    elif op == 'index': out = el(u.src[0], tuple(low(j) for j in u.src[1:]) + idx)", "    elif op == 'index': out = el(u.src[0], idx + tuple(low(j) for j in u.src[1:]))")]),
  ("w5 render unflat stride",     [("else A('div', f, c(stride)))", "else A('div', f, c(stride * d)))")]),
  ("w5 render flat_of order",     [("    for i, d in zip(idx, shape): f = add(mul(f, d), i)", "    for i, d in zip(reversed(idx), reversed(shape)): f = add(mul(f, d), i)")]),
  ("w5 render reshape same rank skipped", [("out = el(u.src[0], idx if xs == u.shape else unflat(flat_of(idx, u.shape), xs))", "out = el(u.src[0], idx if len(xs) == len(u.shape) else unflat(flat_of(idx, u.shape), xs))")]),
  ("w5 render permute inverse",   [("      for kk, p_ in enumerate(u.arg): s_[p_] = idx[kk]", "      for kk, p_ in enumerate(u.arg): s_[kk] = idx[p_]")]),
  ("w5 render pad shift wrong side", [("        sh = add(i, c(-l)) if l else i", "        sh = add(i, c(-r)) if l else i")]),
  # static checks
  ("w5 shrink bounds unchecked",  [("      need(lo >= 0 and hi + sz <= d,", "      need(True,")]),
  ("w5 permute any order",        [("    need(sorted(order) == list(range(len(src[0].shape))),", "    need(len(order) == len(src[0].shape),")]),
  ("w5 reshape count unchecked",  [("    need(prod(to) == prod(src[0].shape),", "    need(True,")]),
  ("w5 pads length unchecked",    [("    need(len(pads) == 2 * len(src[0].shape), \"pads has two numbers (left, right) per axis\")", "    pads = pads + (0,) * max(0, 2 * len(src[0].shape) - len(pads))")]),
  ("w5 stack shapes unchecked",   [("    need(len({s.shape for s in src}) == 1, \"stack operands must share one shape\")", "    pass")]),
  ("w5 index count unchecked",    [("    need(n >= 2 and n - 1 <= len(src[0].shape),", "    need(n >= 2,")]),
  ("w5 shrink offset count unchecked", [("    need(n == 1 + len(x.shape) and 'shape' in attrs,", "    need('shape' in attrs,")]),
  # ---------------- week 6: math, sugar, autodiff, data ----------------
  ("w6 exp2 series one term short", [("p = horner(f, [math.log(2) ** k / math.factorial(k) for k in range(7, -1, -1)])", "p = horner(f, [math.log(2) ** k / math.factorial(k) for k in range(6, -1, -1)])")]),
  ("w6 exp2 rounds n down",         [("    n = floor_(B('add', xc, F(0.5)))", "    n = floor_(xc)")]),
  ("w6 exp2 clamps at -126",        [("    xc = B('where', B('cmplt', xc, F(-150.0)), F(-150.0), xc)", "    xc = B('where', B('cmplt', xc, F(-126.0)), F(-126.0), xc)")]),
  ("w6 exp2 nan becomes 1",         [("    r = B('where', nan, x, B('mul', B('mul', p, two(h)), two(k)))", "    r = B('mul', B('mul', p, two(h)), two(k))")]),
  ("w6 log2 no sqrt2 fold",         [("    big = B('cmplt', F(1.4142135), m)", "    big = B('cmplt', F(2.0), m)")]),
  ("w6 log2 subnormals not scaled", [("    sub = B('cmplt', xs, F(1.1754943508222875e-38))", "    sub = B('cmplt', xs, F(0.0))")]),
  ("w6 log2 zero gives nan",        [("B('where', B('cmplt', x, F(0.0)), F(math.nan), F(-math.inf)))", "B('where', B('cmplt', x, F(0.0)), F(math.nan), F(math.nan)))")]),
  ("w6 sqrt no Newton step",        [("    y = B('mul', B('add', y, B('mul', xs, B('recip', y))), F(0.5))\n", "")]),
  ("w6 sqrt -0.0 loses its sign",   [("B('where', B('cmplt', x, F(0.0)), F(math.nan), x))\n    r = B('where', B('cmplt', x, F(math.inf)), r, x)\n  elif op == 'sin':", "B('where', B('cmplt', x, F(0.0)), F(math.nan), F(0.0)))\n    r = B('where', B('cmplt', x, F(math.inf)), r, x)\n  elif op == 'sin':")]),
  ("w6 sin series one term short",  [("for j in range(6, -1, -1)])", "for j in range(5, -1, -1)])")]),
  ("w6 sin one-part 2pi",           [("B('mul', k, F(-(2 * math.pi - 6.28125))))", "F(0.0))")]),
  ("w6 sin no fold",                [("    r = B('where', B('cmplt', F(math.pi / 2), r), B('add', F(math.pi), nr),", "    r = B('where', B('cmplt', F(math.pi / 2), r), r,")]),
  ("w6 bitcast nan not canonical",  [("CANON_NAN if math.isnan(v) else struct.unpack", "struct.unpack")]),
  ("w6 floor truncates",            [("  t = B('where', B('cmplt', xc, t), B('add', t, K(-1.0)), t)        # below zero, truncation rounded up", "")]),
  ("w6 floor casts big values",     [("B('cmplt', B('max', x, B('mul', x, K(-1.0))), K(8388608.0))", "B('cmplt', B('max', x, B('mul', x, K(-1.0))), K(1e30))")]),
  ("w6 exp uses ln 2",              [("  if op == 'exp': return B('exp2', B('mul', x, F(LOG2E, sh)))", "  if op == 'exp': return B('exp2', B('mul', x, F(LN2, sh)))")]),
  ("w6 cmpeq is cmplt",             [("    return B('where', B('cmplt', x, y), no, B('where', B('cmplt', y, x), no, full(True, 'bool', sh)))", "    return B('cmplt', x, y)")]),
  ("w6 matmul without transpose",   [("B('reshape', A, shape=f\"[{M} {K} 1]\"), order=\"[1 0 2]\")", "B('reshape', A, shape=f\"[{M} {K} 1]\"), order=\"[0 1 2]\")")]),
  ("w6 neg is identity",            [("  if op == 'neg': return B('mul', x, full(-1.0 if x.dtype == 'f32' else -1, x.dtype, sh))", "  if op == 'neg': return x")]),
  ("w6 relu clamps at 1",           [("  if op == 'relu': return B('max', x, full(ZERO[x.dtype], x.dtype, sh))", "  if op == 'relu': return B('max', x, full(1.0 if x.dtype == 'f32' else 1, x.dtype, sh))")]),
  ("w6 grad mul shares swapped",    [("    if op == 'mul': return [(s[0], B('mul', g, s[1])), (s[1], B('mul', g, s[0]))]", "    if op == 'mul': return [(s[0], B('mul', g, s[0])), (s[1], B('mul', g, s[1]))]")]),
  ("w6 grad max tie goes to a",     [("      a, b = s; z, half = K(0.0, sh), B('mul', g, K(0.5, sh))", "      a, b = s; z, half = K(0.0, sh), g")]),
  ("w6 grad recip sign",            [("    if op == 'recip': return [(s[0], B('mul', g, B('mul', B('mul', u, u), K(-1.0, sh))))]", "    if op == 'recip': return [(s[0], B('mul', g, B('mul', u, u)))]")]),
  ("w6 grad exp2 forgets ln 2",     [("    if op == 'exp2': return [(s[0], B('mul', g, B('mul', u, K(LN2, sh))))]", "    if op == 'exp2': return [(s[0], B('mul', g, u))]")]),
  ("w6 grad log2 forgets ln 2",     [("    if op == 'log2': return [(s[0], B('mul', g, B('recip', B('mul', s[0], K(LN2, sh)))))]", "    if op == 'log2': return [(s[0], B('mul', g, B('recip', s[0])))]")]),
  ("w6 grad sqrt forgets the 2",    [("    if op == 'sqrt': return [(s[0], B('mul', g, B('recip', B('mul', u, K(2.0, sh)))))]", "    if op == 'sqrt': return [(s[0], B('mul', g, B('recip', u)))]")]),
  ("w6 grad sin is sin",            [("    if op == 'sin': return [(s[0], B('mul', g, B('sin', B('add', s[0], K(math.pi / 2, sh)))))]", "    if op == 'sin': return [(s[0], B('mul', g, B('sin', s[0])))]")]),
  ("w6 grad where feeds both sides",[("      return [(s[1], B('where', s[0], g, z)), (s[2], B('where', s[0], z, g))]", "      return [(s[1], g), (s[2], g)]")]),
  ("w6 grad detach ignored",        [("    reach[id(u)] = u is x or (u.op != 'detach' and any(reach[id(s)] for s in srcs))", "    reach[id(u)] = u is x or any(reach[id(s)] for s in srcs)")]),
  ("w6 grad shares added last first", [("    gs = parts[id(u)]; g = gs[0]", "    gs = parts[id(u)][::-1]; g = gs[0]")]),
  ("w6 grad expand takes the max",  [("      r = UOp('reduce', (p,), ('add', len(E)), dt, tuple(sh[k] for k in rest))", "      r = UOp('reduce', (p,), ('max', len(E)), dt, tuple(sh[k] for k in rest))")]),
  ("w6 grad reduce max ties not split", [("      share = UOp('expand', (UOp('reshape', (B('mul', g, B('recip', cnt)),), None, dt, (1,) * m + sh),), None, dt, xs)", "      share = UOp('expand', (UOp('reshape', (g,), None, dt, (1,) * m + sh),), None, dt, xs)")]),
  ("w6 grad permute not inverted",  [("      for k, p in enumerate(u.arg): inv[p] = k\n      return", "      for k, p in enumerate(u.arg): inv[k] = p\n      return")]),
  ("w6 grad pad shrinks from the right", [("      return [(s[0], UOp('vshrink', (g,) + tuple(const(u.arg[2 * k], 'i32')", "      return [(s[0], UOp('vshrink', (g,) + tuple(const(u.arg[2 * k + 1], 'i32')")]),
  ("w6 grad shrink pads swapped",   [("for v in (o.arg, d - o.arg - sh[k]))", "for v in (d - o.arg - sh[k], o.arg))")]),
  ("w6 grad index pads swapped",    [("for v in (j.arg, d - 1 - j.arg)) + (0, 0)", "for v in (d - 1 - j.arg, j.arg)) + (0, 0)")]),
  ("w6 grad wrt literal allowed",   [("  need(x.op != 'const', \"can't differentiate with respect to a literal: equal literals are one shared node\")\n", "")]),
  ("w6 grad flows into i32",        [("      if reach[id(a)] and a.dtype == 'f32': parts.setdefault(id(a), []).append(ga)", "      if reach[id(a)]: parts.setdefault(id(a), []).append(ga)")]),
  ("w6 grad seed is 2",             [("  parts = {id(y): [F(1.0)]}", "  parts = {id(y): [F(2.0)]}")]),
  ("w6 url sha unchecked",          [("  if hashlib.sha256(data).hexdigest() != sha: raise UIRError(f\"sha256 mismatch for {url}\")\n", "")]),
  ("w6 url size unchecked",         [("  if len(data) != n * SIZE[dt]: raise UIRError", "  if len(data) < n * SIZE[dt]: raise UIRError")]),
  ("w6 url bool bytes unchecked",   [("  if dt == 'bool' and data.translate(None, b'\\x00\\x01'): raise UIRError(f\"{url}: bool bytes must be 0 or 1\")\n", "")]),
  ("w6 url with data allowed",      [("            if 'data' in attrs: raise UIRError(\"a buffer takes data= or url=, not both\")\n", "")]),
  ("w6 url big-endian",             [("    return iter(struct.unpack(f\"<{self.n}{dict(f32='f', i8='b').get(self.dtype, 'i')}\", b))", "    return iter(struct.unpack(f\">{self.n}{dict(f32='f', i8='b').get(self.dtype, 'i')}\", b))")]),
  ("w6 render bitcast nan not canonical", [("{ int32_t i; if (isnan(x)) return 0x7fc00000; memcpy(&i, &x, 4); return i; }", "{ int32_t i; memcpy(&i, &x, 4); return i; }")]),
  ("w5 render in-place store fused", [("      if any(n.op == 'load' and storage_of(n.src[0]) is storage_of(view) for n in toposort(val)):", "      if False:")]),
  ("w5 render reduce of a broadcast hoisted", [("      a1 = sv(acc1, c(0) if r in opens(xe) else A('mul', r, c(0)))", "      a1 = sv(acc1, c(0))")]),
  # ---------------- week 7: axes, threads, speed ----------------
  ("w7 thread rendered as a plain loop", [("        _, e, r, body = it; ax = axis_of(r)\n        if ax == 'upcast':", "        _, e, r, body = it; ax = axis_of(r); ax = 'loop' if ax == 'thread' else ax\n        if ax == 'upcast':"),
                                          ("  privates = thread_privates(block); private_ids = {id(a) for v in privates.values() for a in v}", "  privates = {}; private_ids = set()")]),
  ("w7 upcast rendered as a plain loop", [("        if ax == 'upcast':                       # unroll: one copy of the body per value, with r a literal", "        if False:")]),
  ("w7 upcast unrolls one copy short", [("          for t in range(r.src[0].arg): name[id(r)] = str(t); emit(body, depth)", "          for t in range(r.src[0].arg - 1): name[id(r)] = str(t); emit(body, depth)")]),
  ("w7 private allocs never reset", [("          for a in privates.get(id(r), ()): mem[id(a)] = [ZERO[a.dtype]] * a.arg[1]\n", "")]),
  ("w7 render private allocs shared", [("        if id(u) not in private_ids:\n          if cuda:", "        if True:\n          if cuda:"),
                                       ("          for a in privates.get(id(r), ()): lines.append(alloc_line(a, '  '))\n          emit(body, 1)", "          emit(body, 1)")]),
  ("w7 thread slice ignores the access size", [("  need(lo >= 0 and hi + size <= S,", "  need(lo >= 0 and hi < S,")]),
  ("w7 thread loads unchecked", [("          if sid in priv or (not w and sid not in written): continue", "          if sid in priv or not w: continue")]),
  ("w7 nested thread loops allowed", [("        if inside: raise UIRError(f\"{axis_of(r)} loop %{r.arg[1]} is inside another parallel loop\")\n", "")]),
  ("w7 mixed strides allowed", [("          if stride.setdefault(sid, S) != S: raise UIRError", "          if False: raise UIRError")]),
  ("w7 upcast bound unchecked", [("    if ax == 'upcast': need(src[0].op == 'const' and 1 <= src[0].arg <= 32,", "    if ax == 'upcast': need(True,")]),
  # ---------------- week 8: GPUs ----------------
  ("w8 cuda no barrier between phases", [("          lines.append(f\"{pad}}}\"); lines.append(f\"{pad}__syncthreads();\")\n          continue\n        if cuda and ax == 'warp':", "          lines.append(f\"{pad}}}\")\n          continue\n        if cuda and ax == 'warp':")]),
  ("w8 cuda shared memory not zeroed", [("\\n{pad}for (int32_t z_ = threadIdx.x; z_ < {u.arg[1]}; z_ += blockDim.x) a{i}[z_] = 0;\\n\"", "\\n\"")]),
  ("w8 cuda local loops run in one thread", [("          bs = next((x[2].src[0].arg * (32 if axis_of(x[2]) == 'warp' else 1) for x in iter_loops(body) if axis_of(x[2]) in PHASE), 1)", "          bs = 1"),
                                            ("          lines.append(f\"{pad}{{\"); lines.append(f\"{pad}  int32_t {rv} = threadIdx.x;\")", "          lines.append(f\"{pad}for (int32_t {rv} = 0; {rv} < {ex(r.src[0])}; {rv}++) {{\")")]),
  ("w8 digits may touch", [("    need(c > rest, f\"can't be shown to keep threads apart:", "    need(c >= rest, f\"can't be shown to keep threads apart:")]),
  ("w8 parallel index may be missing", [("  need(all(top(r) == 0 or exact(r) for r in par),", "  need(True,")]),
  ("w8 div or mod alone pins an index", [("any(op == 'mod' and (k > top(r) or ('div', k) in ds) for op, k in ds)", "any(op in ('div', 'mod') for op, k in ds)")]),
  ("w8 mod never pins an index alone", [("any(op == 'mod' and (k > top(r) or ('div', k) in ds) for op, k in ds)", "any(op == 'mod' and ('div', k) in ds for op, k in ds)")]),
  ("w8 phase loads unchecked", [("    if sid in skip or (not w and sid not in written): continue", "    if sid in skip or not w: continue")]),
  ("w8 store outside local allowed", [("      elif it.op == 'store' and phase != 'local':", "      elif False:")]),
  ("w8 block sizes may differ", [("  if len(sizes) > 1: raise UIRError", "  if False: raise UIRError")]),
  ("w8 local outside global allowed", [("      if axis_of(r) in PHASE and not inside: raise UIRError", "      if axis_of(r) == 'warp' and not inside: raise UIRError")]),
  ("w8 block layouts may differ", [("    if layout.setdefault(sid, f) != f: raise UIRError(f\"{where}: every access", "    if False: raise UIRError(f\"{where}: every access")]),
  ("w9 run mma overwrites C", [("            C[co + i * ldc + j] = wrap(C[co + i * ldc + j] + sum(", "            C[co + i * ldc + j] = wrap(0 + sum(")]),
  ("w9 run mma uses lda for B", [("A_[ao + i * lda + k] * B_[bo + k * ldb + j] for k in range(TILE)", "A_[ao + i * lda + k] * B_[bo + k * lda + j] for k in range(TILE)")]),
  ("w9 run mma transposes B", [("A_[ao + i * lda + k] * B_[bo + k * ldb + j] for k in range(TILE)", "A_[ao + i * lda + k] * B_[bo + j * ldb + k] for k in range(TILE)")]),
  ("w9 render mma overwrites C", [("          lines.append(f\"{pad}  uint32_t s_ = (uint32_t){pc}[{oc} + i_ * {ldc} + j_];\")", "          lines.append(f\"{pad}  uint32_t s_ = 0u;\")")]),
  ("w9 cuda mma overwrites C", [("wmma::load_matrix_sync(fc_, {pc} + {oc}, {ldc}, wmma::mem_row_major);", "wmma::fill_fragment(fc_, 0);")]),
  ("w9 cuda mma B column-major", [("wmma::matrix_b, 16, 16, 16, signed char, wmma::row_major>", "wmma::matrix_b, 16, 16, 16, signed char, wmma::col_major>")]),
  ("w9 cast to i8 saturates", [("  if to == 'i8': return (v + 128) % 256 - 128", "  if to == 'i8': return max(-128, min(127, v))")]),
  ("w9 render i8 as unsigned", [("CT = {'f32': 'float', 'i32': 'int32_t', 'bool': 'bool', 'i8': 'int8_t'}", "CT = {'f32': 'float', 'i32': 'int32_t', 'bool': 'bool', 'i8': 'uint8_t'}")]),
  ("w9 cuda warp loop of n is n threads", [("          bs = next((x[2].src[0].arg * (32 if axis_of(x[2]) == 'warp' else 1)", "          bs = next((x[2].src[0].arg * (1 if axis_of(x[2]) == 'warp' else 1)")]),
  ("w9 cuda no barrier after a warp phase", [("          emit(body, depth + 1); lines.append(f\"{pad}}}\"); lines.append(f\"{pad}__syncthreads();\")", "          emit(body, depth + 1); lines.append(f\"{pad}}}\")")]),
  ("w9 per-thread ignores other threads' reads", [("        except UIRError: bad.add(a); continue", "        except UIRError:\n          if w: bad.add(a)\n          continue")]),
  ("w9 warp loop allowed inside a local loop", [("          if phase: raise UIRError(f\"{ax} loop", "          if phase and not (ax == 'warp' and phase == 'local'): raise UIRError(f\"{ax} loop"), ("        walk(b, phase or (ax if ax in PHASE else None))", "        walk(b, ax if ax in PHASE else phase)")]),
  ("w9 local loop allowed inside a warp loop", [("          if phase: raise UIRError(f\"{ax} loop", "          if phase and not (ax == 'local' and phase == 'warp'): raise UIRError(f\"{ax} loop"), ("        walk(b, phase or (ax if ax in PHASE else None))", "        walk(b, ax if ax in PHASE else phase)")]),
  ("w9 per-thread memory kept in shared memory", [("          if w9: mine.update(per_thread(body, privates.get(id(r), ())))\n", "")]),
  ("w9 per-thread array not zeroed", [("      return f\"{pad}{CT[u.dtype]} a{i}[{mine[id(u)]}] = {{0}};\"", "      return f\"{pad}{CT[u.dtype]} a{i}[{mine[id(u)]}];\"")]),
  ("w9 per-thread offset keeps t * S", [("      o = f\"(int32_t)((uint32_t)({o}) - (uint32_t){name[id(cur[0])]} * {S}u)\"", "      o = o")]),
  ("w9 mma alignment unchecked", [("      need(all(multiple_of(t, 32 if nm != 'C' else 8) for t in ts),", "      need(True,")]),
  ("w9 mma bounds unchecked", [("      need(lo >= 0 and hi + extent(v, ld) <= size,", "      need(lo >= 0,")]),
  ("w9 mma allowed in a local loop", [("      elif it.op == 'mma' and phase != 'warp':", "      elif it.op == 'mma' and phase is None:")]),
  ("w9 store allowed in a warp loop", [("      elif it.op == 'store' and phase != 'local':", "      elif it.op == 'store' and phase is None:")]),
  ("w9 warp outside global allowed", [("      if axis_of(r) in PHASE and not inside: raise UIRError", "      if axis_of(r) == 'local' and not inside: raise UIRError")]),
  ("w9 mma tile ignored by the race check", [("  if ld: digits += [(ld, TILE - 1), (1, TILE - 1)]", "  if False: digits += [(ld, TILE - 1), (1, TILE - 1)]")]),
  ("w9 mma reads unordered", [("      for v in n.src[1:]: loads_of.setdefault(id(version_of(v)), []).append(n)\n", "      pass\n")]),
  ("w9 block size ignores warps", [("          sizes.add(r.src[0].arg * (32 if ax == 'warp' else 1))", "          sizes.add(r.src[0].arg)")]),
  ("w9 i8 data range unchecked", [("c.dtype == 'i32' and -128 <= c.arg <= 127: c = const(c.arg, 'i8')", "c.dtype == 'i32': c = const(c.arg, 'i8')")]),
]

# Generated mutants: every validation in the reference, switched off one at a time. A `need(cond, msg)` becomes
# `need(True or cond, msg)`, and a line ending in `raise UIRError(...)` stops raising. Each one stands for a student
# compiler that forgot one rule, so some test must notice. Opt in with --checks (they take a few more minutes).
def auto_mutants():
  out, lines = [], SRC.split('\n')
  for k, ln in enumerate(lines):
    if SRC.count(ln + '\n') != 1: continue
    m = re.match(r"(\s*)need\((.*)", ln)
    if m: out.append((f"check off, line {k + 1}: {ln.strip()[:70]}", [(ln + '\n', f"{m.group(1)}need(True or {m.group(2)}" + '\n')])); continue
    m = re.search(r"raise UIRError\(.*\)( from None)?\s*$", ln)
    if m and not ln.strip().startswith('except'): out.append((f"check off, line {k + 1}: {ln.strip()[:70]}", [(ln + '\n', ln[:m.start()] + 'pass' + '\n')]))
  # and every rewrite rule of the simplifier, switched off: a student who forgot that rule must fail some test
  i, j = SRC.index('def rewrite_one'), SRC.index('def simplify')
  for ln in SRC[i:j].split('\n'):
    m = re.search(r":\s*return (?!None)(.*)$", ln)
    if m and SRC.count(ln + '\n') == 1:
      out.append((f"rule off: {ln.strip()[:80]}", [(ln + '\n', ln[:m.start()] + ': return None' + '\n')]))
  return out
AUTO = auto_mutants()

def apply(muts):
  s = SRC
  for old, new in muts:
    if s.count(old) != 1: raise SystemExit(f"mutant pattern must match once, matched {s.count(old)}: {old!r}")
    s = s.replace(old, new)
  return s

# ---------------- the runner ----------------
# Each mutant runs in its own short-lived process (so a hang or a memory blowup can't take the run down), and
# inside it every test is graded in-process: the mutated compiler is loaded as a module and tools/test.py's own
# graders are pointed at it, so a test costs milliseconds instead of a Python start-up. A render test only
# compiles C when the mutant changed the C, because identical C gives the reference's (passing) result.
# The MNIST test is skipped: it is an end-to-end check whose parts the other tests cover, and it costs 30 s.
SKIP = ('mnist_train',)
TIMEOUT = 2400 if os.environ.get('UIR_CUDA_DOCKER') else 300   # seconds per mutant: a hang counts as killed

def test_files():
  fs = sorted(glob.glob(os.path.join(ROOT, 'tests', 'week*', '**', '*.uir'), recursive=True))
  return [f for f in fs if not any(s in f for s in SKIP)]

def week_of(f): return int(f.replace('\\', '/').split('/tests/week')[1].split('/')[0])

def worker(index, ref_c_path, matrix):
  import io, shutil, importlib.util, contextlib
  sys.setrecursionlimit(100000); threading.stack_size(128 * 1024 * 1024)
  out = {}
  def body():
    name, muts = (M + AUTO)[index] if index >= 0 else ('control', [])
    code = apply(muts)
    spec = importlib.util.spec_from_loader('mutant', loader=None); Mu = importlib.util.module_from_spec(spec)
    exec(compile(code, os.path.join(HERE, 'uirc.py'), 'exec'), Mu.__dict__)
    ts = importlib.util.spec_from_file_location('grader', os.path.join(ROOT, 'tools', 'test.py'))
    T = importlib.util.module_from_spec(ts); ts.loader.exec_module(T)
    ref_c = json.load(open(ref_c_path, encoding='utf-8'))
    def call(cmd, sub, text, base=None, timeout=10):   # tools/test.py's call(), served by the mutant in-process
      d = tempfile.mkdtemp()
      try:
        path = os.path.join(d, 'case.uir'); open(path, 'w', encoding='utf-8', newline='\n').write(text)
        for u in T.url_files(text):
          src = os.path.join(base or ROOT, *u.split('/'))
          if os.path.isfile(src):
            dst = os.path.join(d, *u.split('/')); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copyfile(src, dst)
        o, e = io.StringIO(), io.StringIO()
        try:
          with contextlib.redirect_stdout(o), contextlib.redirect_stderr(e): rc = Mu.main(['uirc', sub, path])
        except Exception as x: rc, e = 3, io.StringIO(f"crash: {type(x).__name__}: {x}")
        return rc, o.getvalue(), e.getvalue()
      finally: shutil.rmtree(d, ignore_errors=True)
    T.call = call
    first = int(name[1]) if name[:1] == 'w' and name[1:2].isdigit() else 1
    fs = sorted(test_files(), key=lambda f: (week_of(f) != first, f))
    fails = []
    for f in fs:
      text, h = Mu.read_text(f), T.headers(Mu.read_text(f))
      rel = os.path.relpath(f, ROOT).replace('\\', '/')
      try:
        if h.get('render'):
          rc, c, _ = call(None, 'render', text, os.path.dirname(f), 10)
          bad = None if rc == 0 and c == ref_c.get(rel) else T.grade_render(None, text, os.path.dirname(f), h)
        else: bad = T.grade(None, f)
      except Exception as x: bad = f"crash: {x}"
      if bad:
        fails.append(rel)
        if not matrix and name != 'control': break
    out.update(name=name, killed=bool(fails), fails=fails)
  def safe():
    try: body()
    except BaseException as x:                   # a mutant that can't even load or run counts as caught, with the reason
      name = (M + AUTO)[index][0] if index >= 0 else 'control'
      out.update(name=name, killed=True, fails=[f"(the mutated compiler crashed: {type(x).__name__}: {str(x)[:120]})"])
  t = threading.Thread(target=safe); t.start(); t.join()
  print(json.dumps(out))

def reference_c(path):
  # the reference's C for every render test, once: a mutant whose C is identical can't change the verdict
  import importlib.util
  sys.setrecursionlimit(100000)
  spec = importlib.util.spec_from_file_location('ref', os.path.join(HERE, 'uirc.py')); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
  out = {}
  for f in test_files():
    text = R.read_text(f)
    if not re.search(r"^#\s*render", text, re.M): continue
    try: out[os.path.relpath(f, ROOT).replace('\\', '/')] = R.render_c(R.parse(text, os.path.dirname(f))[0])
    except R.UIRError: pass
  json.dump(out, open(path, 'w', encoding='utf-8'))

def run_one(i, ref, matrix):
  try:
    p = subprocess.run([sys.executable, os.path.abspath(__file__), '--worker', str(i), ref] + (['--matrix'] if matrix else []),
                       capture_output=True, text=True, timeout=TIMEOUT)
    return json.loads(p.stdout.strip().splitlines()[-1])
  except subprocess.TimeoutExpired: return {'name': (M + AUTO)[i][0] if i >= 0 else 'control', 'killed': True, 'fails': ['(timed out)']}
  except (IndexError, ValueError): return {'name': (M + AUTO)[i][0] if i >= 0 else 'control', 'killed': True, 'fails': [f'(worker crashed: {p.stderr.strip()[-200:]})']}

if __name__ == '__main__':
  import re, time
  if sys.argv[1:2] == ['--worker']: worker(int(sys.argv[2]), sys.argv[3], '--matrix' in sys.argv); sys.exit(0)
  matrix = '--matrix' in sys.argv            # every mutant against every test: which tests catch what
  only = [a for a in sys.argv[1:] if not a.startswith('--')]
  jobs = int(next((a.split('=')[1] for a in sys.argv if a.startswith('--jobs=')), max(1, min(6, (os.cpu_count() or 2) - 1))))
  t0 = time.time()
  with tempfile.TemporaryDirectory() as tmp:
    for n_, muts_ in M + AUTO:                 # a mutant that no longer applies must fail loudly, never count as caught
      try: compile(apply(muts_), 'mutant', 'exec')
      except SyntaxError as x: raise SystemExit(f"mutant {n_!r} doesn't compile: {x}")
    ref = os.path.join(tmp, 'ref_c.json'); reference_c(ref)
    ctrl = run_one(-1, ref, True)
    if ctrl['killed']: raise SystemExit(f"control (the unmutated reference) fails its own tests: {ctrl['fails'][:5]}")
    pool = M + AUTO if '--checks' in sys.argv else M
    todo = [i for i, (n, _) in enumerate(pool) if not only or any(o in n for o in only)]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=jobs) as ex: res = list(ex.map(lambda i: run_one(i, ref, matrix), todo))
  for r in res:
    if not r['killed']: print(f"SURVIVED  {r['name']}")
  if matrix or not only:                      # the test guides read this: which bugs each test is known to catch
    json.dump({'matrix': matrix, 'entries': {r['name']: r for r in res}}, open(os.path.join(HERE, '.mutant_results.json'), 'w', encoding='utf-8'), indent=0)
  alive = sum(not r['killed'] for r in res)
  print(f"\n{len(res) - alive} / {len(res)} mutants killed, control passed, {time.time() - t0:.0f} s")
  sys.exit(1 if alive else 0)
