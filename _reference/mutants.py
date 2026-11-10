# SPOILERS. Proves the week 1 to 5 suites have teeth: each mutant plants one plausible student bug in the
# reference compiler, and the suite must catch (kill) every one. Run: python _reference/mutants.py
import os, sys, json, glob, hashlib, threading, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
WORKERS, JOBS = 2, 2   # mutants at once, tests per mutant at once: keep memory modest
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SRC = open(os.path.join(HERE, 'uirc.py'), encoding='utf-8').read()
WEEKS = (1, 2, 3, 4, 5)

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
  ("w4 render skips rangeify",    [("u.op == 'range' or u.op in SHAPE_OPS or (u.op in ALU and u.shape) or len(u.shape) >= 2", "u.op == 'range'"), (" or (len(u.shape) == 1 and u.shape[0] > 32 and u.op not in MEM) for u in all_nodes(names))", " for u in all_nodes(names))")]),
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
  ("w2 unsequenced store ok",     [("    if u.op == 'store' and id(u) not in sequenced: raise", "    if False: raise")]),
  ("w2 duplicate slots ok",       [("  if len(slots) != len(set(slots)): raise", "  if False: raise")]),
  ("w2 after version unchecked",  [("if src[1].op == 'store': need(version_of(src[1].src[0]) is src[0], ", "if src[1].op == 'store': need(True, ")]),
  ("w2 memory in call body ok",   [("    need(not any(u.op in MEM or u.op in ('load', 'store') for u in toposort(body, into_bodies=True)), ", "    need(True, ")]),
  ("w2 memory as ALU operand ok", [("  if op not in ('shrink', 'load', 'store', 'after'): need(not any(is_mem(s) for s in src), ", "  if False: need(True, ")]),
  ("w2 store type unchecked",     [("    need((src[0].dtype, src[0].shape) == (src[1].dtype, src[1].shape), ", "    need(True, ")]),
  ("w2 data length unchecked",    [("            if len(toks) != n: raise", "            if False: raise")]),
  ("w2 data dtype unchecked",     [("              if c is None or c.dtype != dt: raise", "              if c is None: raise")]),
  ("w2 no ordering cycle check",  [("      if st == 1: raise UIRError(\"a load of an old", "      if False: raise UIRError(\"a load of an old")]),
  # ---------------- week 2: renderer ----------------
  ("w2 loads not before stores",  [("    if n.op == 'store': d += [", "    if False: d += [")]),
  ("w2 C plain signed add",       [("      e = f\"(int32_t)((uint32_t){a[0]} {dict(add='+', mul='*', shl='<<')[op]} (uint32_t){a[1]})\"",
                                    "      e = f\"({a[0]} {dict(add='+', mul='*', shl='<<')[op]} {a[1]})\"")]),
  ("w2 C div without -1 guard",   [("    elif op == 'div': e = f\"({a[1]} == -1 ? (int32_t)(0u - (uint32_t){a[0]}) : {a[0]} / {a[1]})\"", "    elif op == 'div': e = f\"({a[0]} / {a[1]})\"")]),
  ("w2 C mod without -1 guard",   [("    elif op == 'mod': e = f\"({a[1]} == -1 ? 0 : {a[0]} % {a[1]})\"", "    elif op == 'mod': e = f\"({a[0]} % {a[1]})\"")]),
  ("w2 C max ignores nan",        [("  if (isnan(a) || isnan(b)) return NAN;\n", "")]),
  ("w2 C max ignores -0.0",       [("  if (a == 0.0f && b == 0.0f) return signbit(a) ? b : a;", "")]),
  ("w2 C cast to i32 rounds",     [("else f\"(({t}){a[0]})\"", "else f\"(({t})lrintf({a[0]}))\"")]),
  ("w2 C float literals 6 digits",[("  return float.hex(v) + 'f'", "  return ('%.6g' % v) + ('' if any(ch in '%.6g' % v for ch in '.en') else '.0') + 'f'")]),
  ("w2 C alloc not zeroed",       [("lines.append(f\"{pad}{t} a{i}[{u.arg[1]}] = {{0}};\")", "lines.append(f\"{pad}{t} a{i}[{u.arg[1]}] = {{1}};\")")]),
  ("w2 C rank-1 store one elem",  [("        if u.src[0].shape: lines.extend(f\"{pad}{p}[{o} + {j}] = {x}[{j}];\" for j in range(u.src[0].shape[0]))",
                                    "        if u.src[0].shape: lines.append(f\"{pad}{p}[{o}] = {x}[0];\")")]),
  ("w2 C rank-1 load no offset",  [("', '.join(f\"{p}[{o} + {j}]\" for j in range(u.shape[0]))", "', '.join(f\"{p}[{j}]\" for j in range(u.shape[0]))")]),
  ("w2 C nested offsets lost",    [("    return p, (off if o == '0' else f\"{o} + {off}\")", "    return p, off")]),
  ("w2 C where swapped",          [("    elif op == 'where': e = f\"({a[0]} ? {a[1]} : {a[2]})\"", "    elif op == 'where': e = f\"({a[0]} ? {a[2]} : {a[1]})\"")]),
  ("w2 C cmplt as <=",            [("    elif op == 'cmplt': e = f\"({a[0]} < {a[1]})\"", "    elif op == 'cmplt': e = f\"({a[0]} <= {a[1]})\"")]),
  # ---------------- week 3: loops ----------------
  ("w3 loads never move into loops",      [("      paths[id(n)] = P\n", "      pass\n")]),
  ("w3 loads follow their deepest use",   [("base, P = paths[id(n)], common([paths[id(c)] for c in cons[id(n)]])", "base, P = paths[id(n)], max([paths[id(c)] for c in cons[id(n)]], key=len)")]),
  ("w3 placement sees only the roots",    [("  for r in universe:\n", "  for r in ():\n")]),
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
]

def apply(muts):
  s = SRC
  for old, new in muts:
    if s.count(old) != 1: raise SystemExit(f"mutant pattern must match once, matched {s.count(old)}: {old!r}")
    s = s.replace(old, new)
  return s

def kill(i_name_muts, tmp):
  i, (name, muts) = i_name_muts
  path = os.path.join(tmp, f"m{i}", "uirc.py"); os.makedirs(os.path.dirname(path))
  open(path, 'w', encoding='utf-8').write(apply(muts))
  comp = f'"{sys.executable}" "{path}"' if os.name == 'nt' else f"{sys.executable} {path}"
  fails, killed = [], False
  # a "wN ..." mutant is tried against week N first: same verdict (killed if any week fails), far less work
  first = int(name[1]) if name[:1] == 'w' and name[1:2].isdigit() and name[2:3] == ' ' else WEEKS[0]
  for week in [first] + [w for w in WEEKS if w != first]:   # the control must pass them all
    p = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'test.py'), '--compiler', comp, '--week', str(week), '--jobs', str(JOBS)],
                       capture_output=True, text=True, cwd=ROOT)
    fails += [l.split()[1] for l in p.stdout.splitlines() if l.startswith('FAIL ')]
    killed = killed or p.returncode != 0
    if killed and name != 'control': break
  return name, killed, fails

# Results are cached per mutant, keyed by a hash of the oracle, the tools, every test, and the mutant itself,
# so a run that gets killed (this machine runs low on memory) resumes where it stopped. Any change to the
# oracle, the grader or a test invalidates every entry. --fresh ignores the cache.
CACHE = os.path.join(HERE, '.mutant_cache.json')
def fingerprint():
  h = hashlib.sha256(SRC.encode())
  for f in sorted(glob.glob(os.path.join(ROOT, 'tests', '**', '*.uir'), recursive=True)) + [os.path.join(ROOT, 'tools', 'test.py')]:
    h.update(f.replace(os.sep, '/').encode()); h.update(open(f, 'rb').read())
  return h.hexdigest()
def load_cache(fp):
  try:
    c = json.load(open(CACHE, encoding='utf-8'))
    return c['entries'] if c.get('fingerprint') == fp else {}
  except (OSError, ValueError, KeyError): return {}
def save_cache(fp, entries):
  tmp = CACHE + '.tmp'
  json.dump({'fingerprint': fp, 'entries': entries}, open(tmp, 'w', encoding='utf-8'))
  os.replace(tmp, CACHE)
def key(name, muts): return hashlib.sha256(json.dumps([name, muts]).encode()).hexdigest()

if __name__ == '__main__':
  fp = fingerprint()
  entries = {} if '--fresh' in sys.argv else load_cache(fp)
  lock = threading.Lock()
  with tempfile.TemporaryDirectory() as tmp, ThreadPoolExecutor(max_workers=WORKERS) as ex:
    if entries.get('control') != 'passed':                           # an unmutated copy must pass, or every 'kill' is fake
      _, ctrl_failed, fails = kill((len(M), ("control", [])), tmp)
      if ctrl_failed: raise SystemExit(f"control (unmutated reference) failed the suite: {fails[:5]}")
      entries['control'] = 'passed'; save_cache(fp, entries)
    todo = [(i, m) for i, m in enumerate(M) if key(*m) not in entries]
    print(f"{len(M) - len(todo)} cached, {len(todo)} to run", flush=True)
    def run_one(x):
      name, killed, fails = kill(x, tmp)
      with lock:
        entries[key(*x[1])] = {'name': name, 'killed': killed, 'fails': fails[:3]}; save_cache(fp, entries)
        print(f"  {'killed' if killed else 'SURVIVED'} {name}", flush=True)
      return name
    list(ex.map(run_one, todo))
  res = [entries[key(*m)] for m in M]
  for r in res:
    if not r['killed']: print(f"SURVIVED  {r['name']}")
  alive = [r['name'] for r in res if not r['killed']]
  print()
  print(f"{len(res) - len(alive)} / {len(res)} mutants killed (control passed all weeks)")
  sys.exit(1 if alive else 0)
