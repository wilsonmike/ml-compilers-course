# SPOILERS. This is the reference compiler for the course. If you are taking the course, do not read it.
# It doubles as the oracle: `python _reference/uirc.py run FILE` / `simplify FILE` / `render FILE` (weeks 2-3).
import sys, os, re, math, struct, random, threading, itertools, hashlib

class UIRError(Exception): pass          # invalid program -> exit 2
class AssertFail(Exception): pass        # a failing assert -> exit 1

INT_MIN, INT_MAX = -2**31, 2**31 - 1
def wrap(x): return (x - INT_MIN) % 2**32 + INT_MIN
def f32(x):
  try: return struct.unpack('f', struct.pack('f', x))[0]
  except OverflowError: return math.copysign(math.inf, x)   # pack only raises when the f32 rounding is inf
def tdiv(a, b): return abs(a) // abs(b) * (1 if (a < 0) == (b < 0) else -1)   # C truncates toward zero
def fbits(x): return struct.pack('f', x)                     # hashable identity: keeps -0.0 and nan stable
def argkey(a):
  # hash-cons key for an arg: floats by bit pattern at any depth (data=[-0.0] must not merge with data=[0.0])
  if isinstance(a, float): return ('f', fbits(a))
  if isinstance(a, tuple): return tuple(argkey(x) for x in a)
  return a

# ---------------- the UOp, hash consed ----------------

MATH = {'exp2', 'log2', 'sqrt', 'sin'}           # week 6: defined by exact expansions (math_body)
ALU = {'cast', 'recip', 'add', 'mul', 'max', 'xor', 'cmplt', 'shl', 'div', 'mod', 'where', 'bitcast', 'detach'} | MATH
STORAGE = {'buffer', 'alloc', 'after'}           # a whole version of some memory
MEM = STORAGE | {'shrink'}                       # addrspace GLOBAL: memory, not values
def is_mem(u): return u.op in MEM
def version_of(v):
  while v.op == 'shrink': v = v.src[0]
  return v
def storage_of(v):
  v = version_of(v)
  while v.op == 'after': v = v.src[0]
  return v
NUM = ('i32', 'f32')

class UOp:
  _cache, _lock = {}, threading.Lock()
  __slots__ = ('op', 'src', 'arg', 'dtype', 'shape')
  def __new__(cls, op, src=(), arg=None, dtype=None, shape=()):
    key = (op, tuple(id(s) for s in src), argkey(arg), dtype, shape)
    with UOp._lock:
      if (u := UOp._cache.get(key)) is not None: return u
      u = object.__new__(cls)
      u.op, u.src, u.arg, u.dtype, u.shape = op, tuple(src), arg, dtype, shape
      UOp._cache[key] = u   # cache holds a strong ref to src, so ids stay valid
      return u
  def __repr__(self): return f"UOp({self.op}, {self.dtype}{list(self.shape)}, arg={self.arg!r}, nsrc={len(self.src)})"

EFFECT = {'store', 'end'}
_OPEN = {}
def opens(u):
  # the ranges u depends on that no end has closed yet (week 3). Memoized forever: nodes are immortal.
  if id(u) in _OPEN: return _OPEN[id(u)]
  stack = [(u, False)]                           # post-order, but never below a node already known
  while stack:
    x, done = stack.pop()
    if id(x) in _OPEN: continue
    srcs = x.src[1:] if x.op == 'call' else x.src
    if not done:
      stack.append((x, True)); stack.extend((y, False) for y in srcs if id(y) not in _OPEN); continue
    o = frozenset().union(*(_OPEN[id(y)] for y in srcs)) if srcs else frozenset()
    if x.op == 'range': o = o | {x}
    elif x.op == 'end': o = o - {x.src[-1]}
    _OPEN[id(x)] = o
  return _OPEN[id(u)]

def stores_under(e):
  # the stores an effect runs, looking through ends
  if e.op == 'store': return [e]
  return [st for x in e.src[:-1] for st in stores_under(x)]

def const(v, dtype): return UOp('const', (), f32(float(v)) if dtype == 'f32' else v, dtype, ())

def toposort(root, into_bodies=False, seen=None):
  # iterative post-order. CALL bodies are closed, so by default we don't walk into src[0].
  # Pass one `seen` set across calls to get only the nodes no earlier call returned.
  out, seen, stack = [], (set() if seen is None else seen), [(root, False)]
  while stack:
    u, done = stack.pop()
    if done: out.append(u); continue
    if id(u) in seen: continue
    seen.add(id(u)); stack.append((u, True))
    srcs = u.src if into_bodies or u.op != 'call' else u.src[1:]
    for s in reversed(srcs):
      if id(s) not in seen: stack.append((s, False))
  return out

def free_params(body):
  ps = {}
  for u in toposort(body):
    if u.op == 'param':
      if u.arg in ps and (ps[u.arg].dtype, ps[u.arg].shape) != (u.dtype, u.shape): raise UIRError(f"param {u.arg} used with two types")
      ps[u.arg] = u
  return ps

# ---------------- type rules: build() checks and constructs ----------------

def build(op, src, attrs):
  def need(cond, msg):
    if not cond: raise UIRError(f"{op}: {msg}")
  for s in src: need(s.dtype != 'void' or (op in ('after', 'end') and s.op in EFFECT), "void operand")
  if op not in ('shrink', 'load', 'store', 'after'): need(not any(is_mem(s) for s in src), "memory can't be an operand here (load it first)")
  n = len(src)
  if op in SUGAR:                               # week 6: rewritten into core ops
    return desugar(op, src, need)
  if op == 'gradient':
    need(n == 2, "gradient LOSS X")
    return grad(src[0], src[1])
  if op in ('detach', 'bitcast') or op in MATH:
    need(n == 1, f"{op} takes one operand")
    if op in MATH: need(src[0].dtype == 'f32', "f32 only")
    if src[0].shape: need(not opens(src[0]), "rank-1 values can't depend on an open range")
    if op == 'bitcast':
      need(attrs.get('dtype') in ('i32', 'f32') and src[0].dtype in ('i32', 'f32'), "bitcast X dtype=i32|f32, X i32 or f32")
      return UOp('bitcast', src, None, attrs['dtype'], src[0].shape)
    return UOp(op, src, None, src[0].dtype, src[0].shape)
  if op == 'range':
    need(n == 1 and src[0].dtype == 'i32' and src[0].shape == (), "range N, N an i32 scalar")
    need(not opens(src[0]), "a range's bound can't depend on another range")
    return UOp('range', src, ('range', attrs['_name']), 'i32', ())
  if op == 'end':
    need(n >= 2 and src[-1].op == 'range', "end EFFECT... RANGE")
    need(all(x.op in EFFECT for x in src[:-1]), "end repeats effects: stores or ends")
    need(any(src[-1] in opens(x) for x in src[:-1]), "end closes a range its effects don't use")
    return UOp('end', src, None, 'void', ())
  if op in ('assert', 'call'): need(not any(opens(x) for x in src), f"{op} can't depend on an open range")
  if op in ALU:
    need(len({x.shape for x in src}) == 1, "ALU operands must share one shape (no implicit broadcast: use expand)")
    if src[0].shape: need(not any(opens(x) for x in src), "rank-1 values can't depend on an open range")
  if op in SHAPE_OPS: need(not any(opens(x) for x in src[:1]), "shaped values can't depend on an open range")
  if op == 'expand':
    need(len(src) == 1 and 'shape' in attrs, "expand X shape=[...]")
    to, fr = dims_attr(attrs['shape']), src[0].shape
    need(fr == () or (len(fr) == len(to) and all(a == b or a == 1 for a, b in zip(fr, to))),
         f"can't expand {list(fr)} to {list(to)}: same rank, and only size-1 axes grow")
    return UOp('expand', src, None, src[0].dtype, to)
  if op == 'reduce':
    m = int(attrs.get('pop', '1')) if re.fullmatch(r"[0-9]+", attrs.get('pop', '1'), re.A) else 0
    need(len(src) == 1 and 1 <= m <= len(src[0].shape), "reduce X op=OP [pop=m]: pops m >= 1 leading axes")
    need(attrs.get('op') in ('add', 'mul', 'max'), "reduce needs op=add, op=mul or op=max")
    need(src[0].dtype in NUM, "reduce works on i32 or f32")
    return UOp('reduce', src, (attrs['op'], m), src[0].dtype, src[0].shape[m:])
  if op == 'reshape':
    need(len(src) == 1 and 'shape' in attrs, "reshape X shape=[...]")
    to = dims_attr(attrs['shape'], allow_empty=True)
    need(prod(to) == prod(src[0].shape), f"reshape keeps the element count: {prod(src[0].shape)} != {prod(to)}")
    return UOp('reshape', src, None, src[0].dtype, to)
  if op == 'permute':
    need(len(src) == 1 and 'order' in attrs, "permute X order=[...]")
    order = ints_attr(attrs['order'])
    need(sorted(order) == list(range(len(src[0].shape))), f"order must be a permutation of 0..{len(src[0].shape) - 1}")
    return UOp('permute', src, order, src[0].dtype, tuple(src[0].shape[p] for p in order))
  if op == 'pad':
    need(len(src) == 1 and 'pads' in attrs, "pad X pads=[l0 r0 l1 r1 ...]")
    pads = ints_attr(attrs['pads'])
    need(len(pads) == 2 * len(src[0].shape), "pads has two numbers (left, right) per axis")
    return UOp('pad', src, pads, src[0].dtype, tuple(d + pads[2 * k] + pads[2 * k + 1] for k, d in enumerate(src[0].shape)))
  if op == 'stage':
    need(len(src) == 1, "stage X")
    return UOp('stage', src, None, src[0].dtype, src[0].shape)
  n = len(src)
  if op == 'shrink' and src and not is_mem(src[0]):  # week 5: a window into a value, offsets symbolic but provable
    x = src[0]
    need(n == 1 + len(x.shape) and 'shape' in attrs, "shrink X o0 ... o(r-1) shape=[...]: one offset per axis")
    to = dims_attr(attrs['shape'], allow_empty=not x.shape)
    need(len(to) == len(x.shape), "shrink keeps the rank")
    for k, (o, d, sz) in enumerate(zip(src[1:], x.shape, to)):
      need(o.dtype == 'i32' and o.shape == () and not is_mem(o), "offsets are i32 scalars")
      lo, hi = bounds(o, {})
      need(lo >= 0 and hi + sz <= d, f"can't prove axis {k} is in bounds: offset in [{lo}, {hi}], {sz} element(s) of {d}")
    return UOp('vshrink', src, None, x.dtype, to)
  if op == 'shrink':
    need(n == 2 and is_mem(src[0]), "shrink MEM OFFSET shape=[k]")
    need(not is_mem(src[1]) and src[1].dtype == 'i32' and src[1].shape == (), "the offset must be an i32 scalar")
    need('shape' in attrs, "shrink needs shape=[k] or shape=[]")
    shape = () if re.fullmatch(r"\[[ \t]*\]", attrs['shape']) else shape_attr(attrs['shape'])
    k, plen = (shape[0] if shape else 1), (src[0].shape[0] if src[0].shape else 1)
    lo, hi = bounds(src[1], {})
    need(lo >= 0 and hi + k <= plen, f"can't prove the view is in bounds: offset in [{lo}, {hi}], {k} element(s), parent has {plen}")
    return UOp('shrink', src, None, src[0].dtype, shape)
  if op == 'load':
    need(n == 1 and is_mem(src[0]), "load MEM")
    return UOp('load', src, None, src[0].dtype, src[0].shape)
  if op == 'store':
    need(n == 2 and is_mem(src[0]) and not is_mem(src[1]), "store MEM VALUE")
    need((src[0].dtype, src[0].shape) == (src[1].dtype, src[1].shape), "the value must match the view's dtype and shape")
    return UOp('store', src, None, 'void', ())
  if op == 'after':
    need(n == 2 and src[0].op in STORAGE and src[1].op in EFFECT, "after MEM EFFECT, MEM a whole buffer version (not a view)")
    sts = stores_under(src[1])
    if src[1].op == 'store': need(version_of(src[1].src[0]) is src[0], "the store must write into the version after names")
    else:
      need(any(storage_of(st.src[0]) is storage_of(src[0]) for st in sts), "the loop must store into the memory after names")
      # and into the version after names: each such store writes into that version, or into a version built inside
      # this loop on top of it (an inner after has the loop's range open). Anything else forks the version chain.
      r = src[1].src[-1]
      def entry(v):
        v = version_of(v)
        while v.op == 'after' and r in opens(v): v = v.src[0]
        return v
      need(all(entry(st.src[0]) is src[0] for st in sts if storage_of(st.src[0]) is storage_of(src[0])),
           "the loop must store into the version after names, not an older one")
    return UOp('after', src, None, src[0].dtype, src[0].shape)
  if op == 'const':
    raise UIRError("const takes a literal")   # handled by the parser
  if op == 'param':
    raise UIRError("param takes a slot")      # handled by the parser
  if op == 'call':
    need(n >= 1, "needs a body")
    body, args = src[0], src[1:]
    need(not any(u.op in MEM or u.op in ('load', 'store') for u in toposort(body, into_bodies=True)), "memory can't be used inside a call body")
    for slot, p in free_params(body).items():
      need(slot < len(args), f"no arg for param {slot}")
      need((args[slot].dtype, args[slot].shape) == (p.dtype, p.shape), f"arg {slot} type mismatch")
    return UOp('call', src, None, body.dtype, body.shape)
  if op == 'stack':
    need(n >= 1, "needs operands")
    need(len({s.shape for s in src}) == 1, "stack operands must share one shape")
    need(len({s.dtype for s in src}) == 1, "dtype mismatch")
    return UOp('stack', src, None, src[0].dtype, (n,) + src[0].shape)
  if op == 'index':
    need(n >= 2 and n - 1 <= len(src[0].shape), "index X j0 ...: at most one index per axis")
    need(all(j.dtype == 'i32' and j.shape == () for j in src[1:]), "indices are i32 scalars")
    return UOp('index', src, None, src[0].dtype, src[0].shape[n - 1:])
  if op == 'cast':
    need(n == 1 and attrs.get('dtype') in ('bool', 'i32', 'f32'), "cast a dtype=D")
    return UOp('cast', src, None, attrs['dtype'], src[0].shape)
  if op == 'recip':
    need(n == 1 and src[0].dtype == 'f32', "f32 only")
    return UOp('recip', src, None, 'f32', src[0].shape)
  if op == 'where':
    need(n == 3 and src[0].dtype == 'bool' and src[1].dtype == src[2].dtype, "where bool a b")
    return UOp('where', src, None, src[1].dtype, src[1].shape)
  if op == 'assert':
    need(n == 2 and src[0].dtype == src[1].dtype and src[0].shape == src[1].shape, "assert a b, same type")
    return UOp('assert', src, None, 'void', ())
  ok = {'add': NUM, 'mul': NUM, 'max': NUM, 'cmplt': NUM, 'xor': ('i32', 'bool'), 'shl': ('i32',), 'div': ('i32',), 'mod': ('i32',)}
  need(op in ok, "unknown op")
  need(n == 2 and src[0].dtype == src[1].dtype, "two operands of the same dtype")
  need(src[0].dtype in ok[op], f"bad dtype {src[0].dtype}")
  return UOp(op, src, None, 'bool' if op == 'cmplt' else src[0].dtype, src[0].shape)

# ---------------- ALU semantics ----------------

def do_cast(v, frm, to):
  if frm == to: return v
  if to == 'bool': return v != 0
  if frm == 'bool': return int(v) if to == 'i32' else float(v)
  if to == 'f32': return f32(float(v))
  if math.isnan(v) or math.isinf(v) or not (INT_MIN <= math.trunc(v) <= INT_MAX): raise UIRError(f"cast {v} to i32 out of range")
  return math.trunc(v)

CANON_NAN = 0x7fc00000                          # bitcast of any NaN gives this i32 (spec week 6)
def do_bitcast(v, frm, to):
  if frm == to: return v
  if frm == 'f32': return CANON_NAN if math.isnan(v) else struct.unpack('<i', struct.pack('<f', v))[0]
  return struct.unpack('<f', struct.pack('<i', v))[0]

def alu(op, dtypes, vs, out):
  if op == 'detach': return vs[0]
  if op == 'bitcast': return do_bitcast(vs[0], dtypes[0], out)
  if op in MATH: return evaluate(math_body(op), {0: vs[0]})
  if op == 'cast': return do_cast(vs[0], dtypes[0], out)
  if op == 'where': return vs[1] if vs[0] else vs[2]
  a, b = vs[0], vs[1] if len(vs) > 1 else None
  dt = dtypes[0]
  if op == 'recip': return math.copysign(math.inf, a) if a == 0 else f32(1.0 / a)
  if op == 'cmplt': return a < b
  if op == 'xor': return a != b if dt == 'bool' else wrap(a ^ b)
  if op == 'max':
    if dt == 'f32' and (math.isnan(a) or math.isnan(b)): return math.nan
    if a == b == 0 and dt == 'f32': return a if math.copysign(1, a) > 0 else b   # max(-0.0, 0.0) is +0.0 either way
    return a if a > b else b
  if dt == 'f32':
    r = a + b if op == 'add' else a * b
    return math.nan if math.isnan(r) else f32(r)
  if op == 'add': return wrap(a + b)
  if op == 'mul': return wrap(a * b)
  if op == 'shl':
    if not 0 <= b <= 31: raise UIRError("shl out of range")
    return wrap(a << b)
  if b == 0: raise UIRError(f"{op} by zero")
  q = wrap(tdiv(a, b))
  return q if op == 'div' else wrap(a - q * b)

# ---------------- interpreter ----------------

def nflat(v): return [v] if not isinstance(v, tuple) else [y for x in v for y in nflat(x)]
def nest(xs, shape):
  if not shape: return xs[0]
  step = prod(shape[1:])
  return tuple(nest(xs[i * step:(i + 1) * step], shape[1:]) for i in range(shape[0]))
def at(v, idx):
  for i in idx: v = v[i]
  return v
def tabulate(shape, f): return nest([f(idx) for idx in itertools.product(*[range(d) for d in shape])], shape)

def alu_vec(u, v):
  # elementwise over operands of one shared shape (weeks 4-5)
  dts = [x.dtype for x in u.src]
  if not u.shape: return alu(u.op, dts, v, u.dtype)
  fl = [nflat(x) for x in v]
  return nest([alu(u.op, dts, [f[i] for f in fl], u.dtype) for i in range(prod(u.shape))], u.shape)

def fold(op, dt, xs):
  # reduce: a left fold from the first element, rounding after every step
  acc = xs[0]
  for x in xs[1:]: acc = alu(op, [dt, dt], [acc, x], dt)
  return acc

def shaped(u, v):
  # the shape ops (weeks 4-5), shared by evaluate and execute
  x, xs = v[0], u.src[0].shape
  if u.op == 'stage': return x
  if u.op == 'expand': return tabulate(u.shape, lambda i: x if not xs else at(x, tuple(0 if a == 1 else j for a, j in zip(xs, i))))
  if u.op == 'reduce':
    op, m = u.arg; lead = list(itertools.product(*[range(d) for d in xs[:m]]))
    return tabulate(u.shape, lambda r: fold(op, u.dtype, [at(x, l + r) for l in lead]))
  if u.op == 'reshape': return nest(nflat(x), u.shape)
  if u.op == 'permute':
    def src_idx(i):
      s_ = [0] * len(i)
      for k, p in enumerate(u.arg): s_[p] = i[k]
      return tuple(s_)
    return tabulate(u.shape, lambda i: at(x, src_idx(i)))
  if u.op == 'pad':
    pads = u.arg
    def get(i):
      j = tuple(a - pads[2 * k] for k, a in enumerate(i))
      return at(x, j) if all(0 <= a < d for a, d in zip(j, xs)) else ZERO[u.dtype]
    return tabulate(u.shape, get)
  if u.op == 'vshrink': return tabulate(u.shape, lambda i: at(x, tuple(a + o for a, o in zip(i, v[1:]))))
  raise UIRError(f"internal: no shape semantics for {u.op}")

def index_value(v):
  x = v[0]
  for j in v[1:]:
    if not 0 <= j < len(x): raise UIRError(f"index {j} out of range")
    x = x[j]
  return x

def evaluate(root, env):
  # env: slot -> value, or None at the top level. memo is per env: same node, same call, computed once.
  memo = {}
  for u in toposort(root):
    v = [memo[id(s)] for s in (u.src[1:] if u.op == 'call' else u.src)]
    if u.op == 'const': r = u.arg
    elif u.op == 'param':
      if env is None or u.arg not in env: raise UIRError(f"param {u.arg} outside a call")
      r = env[u.arg]
    elif u.op == 'call': r = evaluate(u.src[0], dict(enumerate(v)))
    elif u.op == 'stack': r = tuple(v)
    elif u.op == 'index': r = index_value(v)
    elif u.op == 'assert': r = equal(v[0], v[1])
    elif u.op in IMPURE: raise UIRError(f"internal: {u.op} must go through execute")   # memory and loops run in execute()
    elif u.op in SHAPE_OPS: r = shaped(u, v)
    else: r = alu_vec(u, v)
    memo[id(u)] = r
  return memo[id(root)]

ZERO = {'bool': False, 'i32': 0, 'f32': 0.0}

def equal(a, b):
  if isinstance(a, tuple): return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
  if isinstance(a, float) and math.isnan(a): return isinstance(b, float) and math.isnan(b)
  return a == b

# ---------------- week 6: sugar, math, autodiff, data ----------------

def B(op_, *src, **attrs): return build(op_, list(src), {k: str(v) for k, v in attrs.items()})
def full(v, dt, shape):
  c = const(v, dt)
  return c if not shape else UOp('expand', (c,), None, dt, shape)
def F(v, shape=()): return full(v, 'f32', shape)
LOG2E, LN2 = f32(1 / math.log(2)), f32(math.log(2))

def floor_(x):
  # f32 floor without leaving f32 for big values: |x| >= 2^23 (or inf, nan) is already an integer
  K = lambda v: F(v, x.shape)
  big = B('xor', B('cmplt', B('max', x, B('mul', x, K(-1.0))), K(8388608.0)), full(True, 'bool', x.shape))
  xc = B('where', big, K(0.0), x)
  t = B('cast', B('cast', xc, dtype='i32'), dtype='f32')            # truncates toward zero
  t = B('where', B('cmplt', xc, t), B('add', t, K(-1.0)), t)        # below zero, truncation rounded up
  return B('where', big, x, t)

SUGAR = {'sub', 'neg', 'relu', 'exp', 'log', 'floor', 'fdiv', 'matmul', 'cmpeq'}
def desugar(op, s, need):
  n = len(s)
  need(n == (1 if op in ('neg', 'relu', 'exp', 'log', 'floor') else 2), f"{op} takes {1 if op in ('neg', 'relu', 'exp', 'log', 'floor') else 2} operand(s)")
  x = s[0]; sh = x.shape
  if op in ('exp', 'log', 'floor', 'fdiv'): need(all(v.dtype == 'f32' for v in s), "f32 only")
  if op in ('sub', 'neg', 'relu'): need(x.dtype in NUM, "i32 or f32 only")
  if op == 'neg': return B('mul', x, full(-1.0 if x.dtype == 'f32' else -1, x.dtype, sh))
  if op == 'sub':
    need(s[1].dtype == x.dtype, "two operands of the same dtype")
    return B('add', x, B('mul', s[1], full(-1.0 if x.dtype == 'f32' else -1, x.dtype, s[1].shape)))
  if op == 'relu': return B('max', x, full(ZERO[x.dtype], x.dtype, sh))
  if op == 'fdiv': return B('mul', x, B('recip', s[1]))                 # f32 division: times the reciprocal
  if op == 'exp': return B('exp2', B('mul', x, F(LOG2E, sh)))
  if op == 'log': return B('mul', B('log2', x), F(LN2, sh))
  if op == 'floor': return floor_(x)
  if op == 'cmpeq':
    y = s[1]
    need(x.dtype == y.dtype and x.dtype in ('i32', 'bool'), "cmpeq compares two i32 or two bool values")
    if x.dtype == 'bool': return B('xor', B('xor', x, y), full(True, 'bool', sh))
    no = full(False, 'bool', sh)
    return B('where', B('cmplt', x, y), no, B('where', B('cmplt', y, x), no, full(True, 'bool', sh)))
  if op == 'matmul':                                                     # the week 5 composite, exactly
    A, Bm = s
    need(len(A.shape) == 2 and len(Bm.shape) == 2 and A.shape[1] == Bm.shape[0], "matmul A B: A is MxK, B is KxN")
    M, K = A.shape; N = Bm.shape[1]
    a = B('expand', B('permute', B('reshape', A, shape=f"[{M} {K} 1]"), order="[1 0 2]"), shape=f"[{K} {M} {N}]")
    b = B('expand', B('reshape', Bm, shape=f"[{K} 1 {N}]"), shape=f"[{K} {M} {N}]")
    return B('reduce', B('mul', a, b), op='add', pop=1)
  raise UIRError(f"internal: no sugar for {op}")

def isnan_(x): return B('where', B('cmplt', x, F(math.inf)), const(False, 'bool'), B('where', B('cmplt', F(-math.inf), x), const(False, 'bool'), const(True, 'bool')))
def horner(x, cs):
  p = F(cs[0])
  for c in cs[1:]: p = B('add', B('mul', p, x), F(c))
  return p

_BODY = {}
def math_body(op):
  """The exact definition of each math op, as a graph of core ops on one f32 scalar, param 0."""
  if op in _BODY: return _BODY[op]
  x = UOp('param', (), 0, 'f32', ())
  I = lambda v: const(v, 'i32')
  if op == 'exp2':
    nan = isnan_(x)
    xc = B('where', nan, F(0.0), x)
    xc = B('where', B('cmplt', F(128.0), xc), F(128.0), xc)           # 2^128 is already inf in f32
    xc = B('where', B('cmplt', xc, F(-150.0)), F(-150.0), xc)         # 2^-150 already rounds to 0
    n = floor_(B('add', xc, F(0.5)))                                   # nearest integer
    f = B('add', xc, B('mul', n, F(-1.0)))                             # in [-0.5, 0.5]
    p = horner(f, [math.log(2) ** k / math.factorial(k) for k in range(7, -1, -1)])
    ni = B('cast', n, dtype='i32'); h = B('div', ni, I(2)); k = B('add', ni, B('mul', h, I(-1)))
    two = lambda e: B('bitcast', B('mul', B('add', e, I(127)), I(8388608)), dtype='f32')   # 2^e, e in [-75, 64]
    r = B('where', nan, x, B('mul', B('mul', p, two(h)), two(k)))
  elif op == 'log2':
    ok = B('where', B('cmplt', F(0.0), x), B('cmplt', x, F(math.inf)), const(False, 'bool'))
    xs = B('where', ok, x, F(1.0))
    sub = B('cmplt', xs, F(1.1754943508222875e-38))                    # subnormal: scale up by 2^23 first
    xn = B('where', sub, B('mul', xs, F(8388608.0)), xs)
    b = B('bitcast', xn, dtype='i32')
    e = B('add', B('div', b, I(8388608)), I(-127))                     # the exponent field
    m = B('bitcast', B('add', B('mod', b, I(8388608)), I(1065353216)), dtype='f32')   # mantissa, in [1, 2)
    big = B('cmplt', F(1.4142135), m)
    m = B('where', big, B('mul', m, F(0.5)), m)                        # in [0.707, 1.414]
    e = B('add', B('cast', B('add', e, B('cast', big, dtype='i32')), dtype='f32'), B('where', sub, F(-23.0), F(0.0)))
    s = B('mul', B('add', m, F(-1.0)), B('recip', B('add', m, F(1.0))))
    q = horner(B('mul', s, s), [2 / (math.log(2) * k) for k in (9, 7, 5, 3, 1)])
    r = B('add', e, B('mul', s, q))
    r = B('where', B('cmplt', F(0.0), x), r, B('where', B('cmplt', x, F(0.0)), F(math.nan), F(-math.inf)))
    r = B('where', B('cmplt', x, F(math.inf)), r, x)
  elif op == 'sqrt':
    ok = B('where', B('cmplt', F(0.0), x), B('cmplt', x, F(math.inf)), const(False, 'bool'))
    xs = B('where', ok, x, F(1.0))
    y = B('exp2', B('mul', B('log2', xs), F(0.5)))                     # a first guess, then one Newton step
    y = B('mul', B('add', y, B('mul', xs, B('recip', y))), F(0.5))
    r = B('where', B('cmplt', F(0.0), x), y, B('where', B('cmplt', x, F(0.0)), F(math.nan), x))
    r = B('where', B('cmplt', x, F(math.inf)), r, x)
  elif op == 'sin':
    fin = B('cmplt', B('max', x, B('mul', x, F(-1.0))), F(math.inf))
    xs = B('where', fin, x, F(0.0))
    k = floor_(B('add', B('mul', xs, F(1 / (2 * math.pi))), F(0.5)))  # turns, rounded
    r = B('add', B('add', xs, B('mul', k, F(-6.28125))), B('mul', k, F(-(2 * math.pi - 6.28125))))
    nr = B('mul', r, F(-1.0))
    r = B('where', B('cmplt', F(math.pi / 2), r), B('add', F(math.pi), nr),
          B('where', B('cmplt', r, F(-math.pi / 2)), B('add', F(-math.pi), nr), r))   # fold into [-pi/2, pi/2]
    r = B('where', B('cmplt', F(math.pi / 2), r), F(math.pi / 2), B('max', r, F(-math.pi / 2)))   # huge x: stay in [-1, 1]
    q = horner(B('mul', r, r), [(-1) ** j / math.factorial(2 * j + 1) for j in range(6, -1, -1)])
    r = B('where', fin, B('mul', r, q), F(math.nan))
  _BODY[op] = r
  return r

def lower_math(roots):
  # replace every math op by its body (render only: run evaluates the bodies directly)
  memo = {}
  def rb(u):
    if id(u) in memo: return memo[id(u)]
    if u.op in MATH and not u.shape: r = rb(substitute(math_body(u.op), (rb(u.src[0]),)))
    elif u.op == 'call': r = u
    else: r = u if not u.src else UOp(u.op, tuple(rb(x) for x in u.src), u.arg, u.dtype, u.shape)
    memo[id(u)] = r; return r
  return [rb(r) for r in roots]

# autodiff: gradients flow through these ops; detach stops them
DIFF = ALU | {'expand', 'reduce', 'reshape', 'permute', 'pad', 'stage', 'vshrink', 'stack', 'index'}

def grad(y, x):
  def need(c, m):
    if not c: raise UIRError(f"gradient: {m}")
  need(not is_mem(y) and y.dtype == 'f32' and y.shape == (), "the first operand (the loss) must be an f32 scalar")
  need(not is_mem(x) and x.dtype == 'f32', "the second operand must be an f32 value")
  need(x.op != 'const', "can't differentiate with respect to a literal: equal literals are one shared node")
  need(not opens(y) and not opens(x), "gradient can't be taken inside a loop")
  order = toposort(y)
  reach = {}
  for u in order:
    srcs = u.src[1:] if u.op == 'call' else u.src
    reach[id(u)] = u is x or (u.op != 'detach' and any(reach[id(s)] for s in srcs))
  zero = F(0.0, x.shape)
  if not reach[id(y)]: return zero
  for u in order:
    if reach[id(u)] and u is not x: need(u.op in DIFF, f"gradients can't flow through {u.op}")
  dt = 'f32'
  def K(v, sh): return F(v, sh)
  def rules(u, g):
    # yields (operand, its share of the gradient), in operand order
    s, op = u.src, u.op; sh = u.shape
    if op == 'add': return [(s[0], g), (s[1], g)]
    if op == 'mul': return [(s[0], B('mul', g, s[1])), (s[1], B('mul', g, s[0]))]
    if op == 'max':
      a, b = s; z, half = K(0.0, sh), B('mul', g, K(0.5, sh))
      return [(a, B('where', B('cmplt', b, a), g, B('where', B('cmplt', a, b), z, half))),
              (b, B('where', B('cmplt', a, b), g, B('where', B('cmplt', b, a), z, half)))]
    if op == 'recip': return [(s[0], B('mul', g, B('mul', B('mul', u, u), K(-1.0, sh))))]
    if op == 'where':
      z = K(0.0, sh)
      return [(s[1], B('where', s[0], g, z)), (s[2], B('where', s[0], z, g))]
    if op in ('cast', 'bitcast'): return [(s[0], g)]                   # f32 to f32 only: other inputs carry no gradient
    if op == 'stage': return [(s[0], UOp('stage', (g,), None, dt, sh))]  # a staged value's gradient is staged too
    if op == 'exp2': return [(s[0], B('mul', g, B('mul', u, K(LN2, sh))))]
    if op == 'log2': return [(s[0], B('mul', g, B('recip', B('mul', s[0], K(LN2, sh)))))]
    if op == 'sqrt': return [(s[0], B('mul', g, B('recip', B('mul', u, K(2.0, sh)))))]
    if op == 'sin': return [(s[0], B('mul', g, B('sin', B('add', s[0], K(math.pi / 2, sh)))))]
    if op == 'reshape': return [(s[0], UOp('reshape', (g,), None, dt, s[0].shape))]
    if op == 'permute':
      inv = [0] * len(u.arg)
      for k, p in enumerate(u.arg): inv[p] = k
      return [(s[0], UOp('permute', (g,), tuple(inv), dt, s[0].shape))]
    if op == 'pad':
      return [(s[0], UOp('vshrink', (g,) + tuple(const(u.arg[2 * k], 'i32') for k in range(len(sh))), None, dt, s[0].shape))]
    if op == 'vshrink':
      need(all(o.op == 'const' for o in s[1:]), "a shrink's offsets must be literals to take its gradient")
      pads = tuple(v for k, (o, d) in enumerate(zip(s[1:], s[0].shape)) for v in (o.arg, d - o.arg - sh[k]))
      return [(s[0], UOp('pad', (g,), pads, dt, s[0].shape))]
    if op == 'expand':
      xs = s[0].shape
      if not xs: return [(s[0], UOp('reduce', (UOp('reshape', (g,), None, dt, (prod(sh),)),), ('add', 1), dt, ()))]
      E = [k for k in range(len(sh)) if xs[k] == 1 and sh[k] != 1]
      if not E: return [(s[0], g)]
      rest = [k for k in range(len(sh)) if k not in E]
      p = UOp('permute', (g,), tuple(E + rest), dt, tuple(sh[k] for k in E + rest))
      r = UOp('reduce', (p,), ('add', len(E)), dt, tuple(sh[k] for k in rest))
      return [(s[0], UOp('reshape', (r,), None, dt, xs))]
    if op == 'reduce':
      rop, m = u.arg; xs = s[0].shape
      ge = UOp('expand', (UOp('reshape', (g,), None, dt, (1,) * m + sh),), None, dt, xs)
      if rop == 'add': return [(s[0], ge)]
      need(rop == 'max', "reduce op=mul has no gradient rule")
      ye = UOp('expand', (UOp('reshape', (u,), None, dt, (1,) * m + sh),), None, dt, xs)
      hit = B('cast', B('xor', B('cmplt', s[0], ye), full(True, 'bool', xs)), dtype='f32')   # 1.0 where x is the max
      cnt = UOp('reduce', (hit,), ('add', m), dt, sh)
      share = UOp('expand', (UOp('reshape', (B('mul', g, B('recip', cnt)),), None, dt, (1,) * m + sh),), None, dt, xs)
      return [(s[0], B('mul', share, hit))]                            # split evenly between tied maxima
    if op == 'stack': return [(a, UOp('index', (g, const(j, 'i32')), None, dt, sh[1:])) for j, a in enumerate(s)]
    if op == 'index':
      need(all(j.op == 'const' and 0 <= j.arg < d for j, d in zip(s[1:], s[0].shape)), "index needs in-range literal indices to take its gradient")
      xs, m = s[0].shape, len(s) - 1
      pads = tuple(v for j, d in zip(s[1:], xs) for v in (j.arg, d - 1 - j.arg)) + (0, 0) * (len(xs) - m)
      return [(s[0], UOp('pad', (UOp('reshape', (g,), None, dt, (1,) * m + sh),), pads, dt, xs))]
    raise UIRError(f"gradient: no rule for {op}")
  parts = {id(y): [F(1.0)]}
  for u in reversed(order):
    if u is x or id(u) not in parts: continue
    gs = parts[id(u)]; g = gs[0]
    for more in gs[1:]: g = B('add', g, more)
    for a, ga in rules(u, g):
      if reach[id(a)] and a.dtype == 'f32': parts.setdefault(id(a), []).append(ga)
  if id(x) not in parts: return zero
  g = parts[id(x)][0]
  for more in parts[id(x)][1:]: g = B('add', g, more)
  return g

# buffers with url= and sha256=: the contents come from a file, checked by hash
CACHE_DIR = os.environ.get('UIR_CACHE') or os.path.join(os.path.expanduser('~'), '.cache', 'uir')
URL_RE = re.compile(r"https://[!-~]+|[A-Za-z0-9_][A-Za-z0-9_.-]*(?:/[A-Za-z0-9_][A-Za-z0-9_.-]*)*", re.A)
SIZE = {'f32': 4, 'i32': 4, 'bool': 1}

class Blob:
  """A buffer's contents from url=. Equal blobs hash cons; values are decoded only when run needs them."""
  __slots__ = ('url', 'sha', 'dtype', 'n', 'path')
  def __init__(self, url, sha, dtype, n, path): self.url, self.sha, self.dtype, self.n, self.path = url, sha, dtype, n, path
  # the path is part of the identity: a node built from a file in one folder must never read another one's
  def __hash__(self): return hash((self.url, self.sha, self.dtype, self.n, self.path))
  def __eq__(self, o): return isinstance(o, Blob) and (self.url, self.sha, self.dtype, self.n, self.path) == (o.url, o.sha, o.dtype, o.n, o.path)
  def __len__(self): return self.n
  def __iter__(self):
    b = open(self.path, 'rb').read()
    if self.dtype == 'bool': return iter([x == 1 for x in b])
    return iter(struct.unpack(f"<{self.n}{'f' if self.dtype == 'f32' else 'i'}", b))

def fetch(url, base):
  if url.startswith('https://'):
    import urllib.request
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, hashlib.sha256(url.encode()).hexdigest()[:32])
    if not os.path.exists(path):
      try:
        with urllib.request.urlopen(url, timeout=120) as r: data = r.read()
      except Exception as e: raise UIRError(f"can't download {url}: {e}") from None
      open(path + '.part', 'wb').write(data); os.replace(path + '.part', path)
    return path
  path = os.path.join(base or '.', *url.split('/'))
  if not os.path.isfile(path): raise UIRError(f"no file {url} next to the program")
  return path

def blob(url, sha, dt, n, base):
  if not URL_RE.fullmatch(url) or '..' in url.split('/'): raise UIRError(f"url must be https://... or a relative path without '..', got {url}")
  if not re.fullmatch(r"[0-9a-f]{64}", sha, re.A): raise UIRError("sha256 must be 64 lowercase hex digits")
  path = fetch(url, base)
  data = open(path, 'rb').read()
  if hashlib.sha256(data).hexdigest() != sha: raise UIRError(f"sha256 mismatch for {url}")
  if len(data) != n * SIZE[dt]: raise UIRError(f"{url} has {len(data)} bytes, a {n}-element {dt} buffer needs {n * SIZE[dt]}")
  if dt == 'bool' and data.translate(None, b'\x00\x01'): raise UIRError(f"{url}: bool bytes must be 0 or 1")
  return Blob(url, sha, dt, n, path)

# ---------------- parser ----------------

# exact lexical grammar (spec section 1). ASCII only.
INT_RE = re.compile(r"-?[0-9]+", re.A)
FLOAT_RE = re.compile(r"-?(?:[0-9]+\.[0-9]*|\.[0-9]+)(?:[eE][-+]?[0-9]+)?|-?[0-9]+[eE][-+]?[0-9]+", re.A)
NAME_RE = re.compile(r"%([A-Za-z0-9_]+)[ \t]*=[ \t]*([a-z_][a-z0-9_]*)(.*)", re.A)
ATTRS = {'const': {'dtype'}, 'param': {'dtype', 'shape'}, 'cast': {'dtype'}, 'bitcast': {'dtype'}, 'buffer': {'dtype', 'slot', 'data', 'url', 'sha256'}, 'alloc': {'dtype'}, 'shrink': {'shape'}, 'expand': {'shape'}, 'reduce': {'op', 'pop'}, 'reshape': {'shape'}, 'permute': {'order'}, 'pad': {'pads'}}
TOK = re.compile(r"[A-Za-z_]+=\[[^\]]*\]|[^ \t]+")

def literal(t):
  if t in ('true', 'false'): return const(t == 'true', 'bool')
  if t in ('inf', '-inf', 'nan'): return const(float(t), 'f32')
  if INT_RE.fullmatch(t):
    if not INT_MIN <= int(t) <= INT_MAX: raise UIRError(f"{t} does not fit in i32")
    return const(int(t), 'i32')
  if FLOAT_RE.fullmatch(t): return const(float(t), 'f32')   # decimal -> f64 -> f32 (spec: rounded twice, on purpose)
  return None

SHAPE_OPS = {'expand', 'reduce', 'reshape', 'permute', 'pad', 'stage', 'vshrink'}
def prod(t):
  r = 1
  for x in t: r *= x
  return r
def ints_attr(v):
  m = re.fullmatch(r"\[[ \t]*((?:[0-9]+[ \t]*)*)\]", v, re.A)
  if not m: raise UIRError(f"expected a list of integers like [2 3], got {v}")
  return tuple(int(x) for x in m.group(1).split())
def dims_attr(v, allow_empty=False):
  d = ints_attr(v)
  if any(x < 1 for x in d) or (not d and not allow_empty): raise UIRError(f"a shape needs positive sizes, got {v}")
  return d

def shape_attr(v):
  m = re.fullmatch(r"\[[ \t]*([0-9]+)[ \t]*\]", v, re.A)
  if not m or int(m.group(1)) < 1: raise UIRError(f"shape must be [k] with k >= 1 in week 1, got {v}")
  return (int(m.group(1)),)

def parse(text, base=None):
  # base: the directory relative url= paths are read from (the program's own folder)
  names, order = {}, []
  for lineno, line in enumerate(text.split('\n'), 1):
    line = line.rstrip('\r').split('#', 1)[0].strip(' \t')
    if not line: continue
    try:
      m = NAME_RE.fullmatch(line)
      if not m: raise UIRError("expected %name = op ...")
      name, op, rest = m.groups()
      if name in names: raise UIRError(f"%{name} defined twice")
      attrs, src = {}, []
      for t in TOK.findall(rest):
        if '=' in t:
          k, v = t.split('=', 1)
          if k not in ATTRS.get(op, set()): raise UIRError(f"{op} has no attribute {k!r}")
          if k in attrs: raise UIRError(f"attribute {k} given twice")
          attrs[k] = v
        elif attrs: raise UIRError("operands come before attributes")
        else: src.append(t)
      if 'dtype' in attrs and attrs['dtype'] not in ('bool', 'i32', 'f32'): raise UIRError(f"bad dtype {attrs['dtype']}")
      if op in ('buffer', 'alloc'):
        if len(src) != 1 or not re.fullmatch(r"[0-9]+", src[0], re.A) or int(src[0]) < 1: raise UIRError(f"{op} N: a size N >= 1")
        n, dt = int(src[0]), attrs.get('dtype')
        if dt is None: raise UIRError(f"{op} needs dtype=")
        if op == 'alloc': u = UOp('alloc', (), ('alloc', n, name), dt, (n,))   # each alloc is its own storage
        else:
          if not re.fullmatch(r"[0-9]+", attrs.get('slot', ''), re.A): raise UIRError("buffer needs slot=N")
          if 'url' in attrs or 'sha256' in attrs:
            if 'url' not in attrs or 'sha256' not in attrs: raise UIRError("url= and sha256= go together")
            if 'data' in attrs: raise UIRError("a buffer takes data= or url=, not both")
            data = blob(attrs['url'], attrs['sha256'], dt, n, base)
          elif 'data' in attrs:
            toks = attrs['data'].strip('[]').split()
            if len(toks) != n: raise UIRError(f"data has {len(toks)} values, the buffer has {n}")
            vals = []
            for t in toks:
              c = literal(t)
              if c is None or c.dtype != dt: raise UIRError(f"data value {t} isn't a {dt} literal")
              vals.append(c.arg)
            data = tuple(vals)
          else: data = (ZERO[dt],) * n
          u = UOp('buffer', (), ('buffer', int(attrs['slot']), n, data, name), dt, (n,))   # each statement is its own buffer, so duplicate slots are caught
      elif op in ('const', 'param'):
        if len(src) != 1: raise UIRError(f"{op} takes one literal")
        dt = attrs.get('dtype')
        if op == 'param':
          if not re.fullmatch(r"[0-9]+", src[0], re.A) or dt is None: raise UIRError("param N dtype=D")
          u = UOp('param', (), int(src[0]), dt, shape_attr(attrs['shape']) if 'shape' in attrs else ())
        else:
          c = literal(src[0])
          if c is None: raise UIRError(f"bad literal {src[0]}")
          if dt is not None and dt != c.dtype:
            if c.dtype == 'f32': raise UIRError("a float literal can't be const i32/bool")
            c = const(do_cast(c.arg, c.dtype, dt), dt)
          u = c
      else:
        args = []
        for t in src:
          if t.startswith('%'):
            if t[1:] not in names: raise UIRError(f"undefined {t}")
            args.append(names[t[1:]])
          elif (c := literal(t)) is not None: args.append(c)
          else: raise UIRError(f"bad operand {t}")
        u = build(op, args, {**attrs, '_name': name})
      free_params(u)          # one slot used with two types is a static error, called or not
      names[name] = u; order.append(name)
    except UIRError as e: raise UIRError(f"line {lineno}: {e}") from None
  check_memory(names)
  return names, order

def all_nodes(names):
  seen, out = set(), []
  for u in names.values(): out += toposort(u, into_bodies=True, seen=seen)
  return out

def check_memory(names):
  # "loads and stores must be fully ordered": one store per version, every store sequenced, each range
  # closed once, outputs outside every loop, and a schedule where loads run before overwriting stores
  nodes = all_nodes(names)
  slots = [u.arg[1] for u in nodes if u.op == 'buffer']
  if len(slots) != len(set(slots)): raise UIRError("two buffers share a slot")
  stores_into, sequenced, closed = {}, set(), {}
  for u in nodes:
    if u.op == 'store': stores_into.setdefault(id(version_of(u.src[0])), []).append(u)
    if u.op == 'after': sequenced.update(id(st) for st in stores_under(u.src[1]))
    if u.op == 'end':
      r = u.src[-1]
      if closed.setdefault(id(r), u) is not u: raise UIRError("a range can be closed by only one end")
  for v, ss in stores_into.items():
    if len(ss) > 1: raise UIRError("two stores into the same buffer version are unordered")
  for u in nodes:
    if u.op in ('store', 'after'):
      for r in opens(u):
        if id(r) not in closed: raise UIRError(f"range %{r.arg[1]} is never closed by an end")
  for u in nodes:
    if u.op == 'store' and id(u) not in sequenced: raise UIRError("a store that no after sequences has no effect")
  for slot, v in final_versions(names).items():
    if opens(v): raise UIRError(f"buffer slot {slot}: its stores' loops are never closed")
  top = [u for u in nodes if not opens(u) and u.op != 'range']
  linearize(top, top)

def linearize(roots, universe=()):
  """Turn a graph into a block of items: nodes, or ('loop', end, range, body). Loops nest as the ends do.
  Inside every block, sources come first, and every load of a version runs before the store that
  overwrites it. This one structure is what run executes and what render prints.
  `universe` is every top-level statement of the program: where a load runs depends on all of its uses,
  not only the ones reachable from these roots, so run (one assert at a time) and render agree."""
  nodes, seen = [], set()
  for r in roots: nodes += toposort(r, seen=seen)
  allnodes, aseen = list(nodes), set(seen)
  for r in universe: allnodes += toposort(r, seen=aseen)
  idx = {id(n): i for i, n in enumerate(nodes)}
  ends = {}
  for n in allnodes:
    if n.op == 'end': ends[id(n.src[-1])] = n
  chains = {}
  def chain(r):                                  # outer-to-inner loop path that ends at range r
    if id(r) in chains: return chains[id(r)]
    if id(r) not in ends: raise UIRError(f"range %{r.arg[1]} is never closed by an end")
    outer = opens(ends[id(r)])
    inner = max(outer, key=lambda q: len(chain(q)), default=None)
    c = (chain(inner) if inner is not None else ()) + (r,)
    if not set(outer) <= set(c[:-1]): raise UIRError(f"ranges don't nest around %{r.arg[1]}")
    chains[id(r)] = c; return c
  def path(n):
    o = opens(n)
    if not o: return ()
    deepest = max(o, key=lambda q: len(chain(q)))
    c = chain(deepest)
    if not o <= set(c): raise UIRError("ranges don't nest: a value depends on two loops that aren't nested")
    return c
  paths = {id(n): path(n) for n in allnodes}
  # a load runs in the innermost loop that holds every use of it. If that loop stores into the version
  # it reads, the load must run every iteration (the accumulator pattern), so it moves into the loop.
  cons, stores_of = {}, {}
  for n in allnodes:
    for z in (n.src[1:] if n.op == 'call' else n.src): cons.setdefault(id(z), []).append(n)
    if n.op == 'store': stores_of.setdefault(id(version_of(n.src[0])), []).append(n)
  def common(ps):
    p = ps[0]
    for q in ps[1:]:
      k = 0
      while k < min(len(p), len(q)) and p[k] is q[k]: k += 1
      p = p[:k]
    return p
  for n in allnodes:
    if n.op != 'load' or id(n) not in cons: continue
    base, P = paths[id(n)], common([paths[id(c)] for c in cons[id(n)]])
    if len(P) <= len(base) or any(a is not b for a, b in zip(P, base)): continue
    inner = base + (P[len(base)],)
    if any(len(paths[id(st)]) >= len(inner) and all(a is b for a, b in zip(paths[id(st)], inner)) for st in stores_of.get(id(version_of(n.src[0])), [])):
      paths[id(n)] = P
  loads_of = {}
  for n in nodes:
    if n.op == 'load': loads_of.setdefault(id(version_of(n.src[0])), []).append(n)
  def deps(n):
    d = list(n.src[1:] if n.op == 'call' else n.src)
    if n.op == 'store': d += [l for l in loads_of.get(id(version_of(n.src[0])), []) if l is not n]
    return d
  def build_block(P):
    def rep_(z):                                 # z as seen from block P: itself, the loop holding it, or outside
      pz = paths[id(z)]
      if pz == P: return None if z.op == 'range' else z
      if len(pz) > len(P) and pz[:len(P)] == P: return ends[id(pz[len(P)])]
      return None
    items = [n for n in nodes if paths[id(n)] == P and n.op != 'range']
    members = {id(n): [n] for n in items}
    for n in nodes:
      if n.op == 'range' and paths[id(n)] == P: continue
      rn = rep_(n)
      if rn is not None and rn is not n: members[id(rn)].append(n)
    for it in items:
      if it.op == 'end': members[id(it)].append(it.src[-1])
    preds = {id(n): set() for n in items}
    for it in items:
      for m in members[id(it)]:
        for z in deps(m):
          rz = rep_(z)
          if rz is not None and rz is not it and id(rz) in preds: preds[id(it)].add(id(rz))
    order, done, state = [], set(), {}
    byid = {id(n): n for n in items}
    for it in sorted(items, key=lambda n: idx[id(n)]):
      stack = [(id(it), iter(sorted(preds[id(it)], key=lambda q: idx[q])))] if id(it) not in state else []
      if stack: state[id(it)] = 1
      while stack:
        q, itr = stack[-1]; nx = next(itr, None)
        if nx is None:
          stack.pop(); state[q] = 2; n = byid[q]
          order.append(('loop', n, n.src[-1], build_block(chain(n.src[-1]))) if n.op == 'end' else n); continue
        st = state.get(nx)
        if st == 1: raise UIRError("a load of an old buffer version is needed after that version was overwritten")
        if st is None: state[nx] = 1; stack.append((nx, iter(sorted(preds[nx], key=lambda q: idx[q]))))
    return order
  return build_block(())

def execute(block, roots_need=None):
  """Run a linearized block on fresh memory. Returns (values, memory)."""
  vals, mem = {}, {}
  def val(x): return x.arg if x.op == 'const' else vals[id(x)]
  def view(v):                                   # (storage id, offset)
    if v.op != 'shrink': return id(storage_of(v)), 0
    sid, off = view(v.src[0]); return sid, off + val(v.src[1])
  def go(items):
    for it in items:
      if isinstance(it, tuple):
        _, e, r, body = it
        for t in range(val(r.src[0])): vals[id(r)] = t; go(body)
        continue
      u = it; op = u.op
      if op in ('const', 'after', 'end', 'range', 'shrink'): continue
      if op == 'buffer': mem[id(u)] = list(u.arg[3]); continue
      if op == 'alloc': mem[id(u)] = [ZERO[u.dtype]] * u.arg[1]; continue
      if op == 'load':
        sid, off = view(u.src[0])
        vals[id(u)] = tuple(mem[sid][off:off + u.shape[0]]) if u.shape else mem[sid][off]; continue
      if op == 'store':
        sid, off = view(u.src[0]); x = val(u.src[1])
        if u.src[0].shape: mem[sid][off:off + len(x)] = list(x)
        else: mem[sid][off] = x
        continue
      v = [val(x) for x in u.src]
      if op == 'stack': vals[id(u)] = tuple(v)
      elif op == 'index': vals[id(u)] = index_value(v)
      elif op == 'assert': vals[id(u)] = equal(v[0], v[1])
      elif op in ('param', 'call'): raise UIRError(f"{op} outside a call")   # calls are inlined before execution
      elif op in SHAPE_OPS: vals[id(u)] = shaped(u, v)
      else: vals[id(u)] = alu_vec(u, v)
  go(block)
  return vals, mem

def final_versions(names):
  # the outputs: for each buffer, the version no top-level after builds on (afters inside loops are local)
  nodes = all_nodes(names); nxt = {}
  for u in nodes:
    if u.op == 'after' and not opens(u): nxt[id(u.src[0])] = u
  outs = {}
  for u in nodes:
    if u.op == 'buffer':
      v = u
      while id(v) in nxt: v = nxt[id(v)]
      outs[u.arg[1]] = v
  return dict(sorted(outs.items()))

def program(names, roots):
  # inline calls once over the roots plus every top-level statement; returns (inlined roots, universe)
  top = [u for u in all_nodes(names) if not opens(u) and u.op != 'range']
  inl = inline_calls(list(roots) + top)
  return inl[:len(roots)], inl[len(roots):]

def final_buffers(names):
  outs = final_versions(names)
  roots, uni = program(names, list(outs.values()))
  _, mem = execute(linearize(roots, uni))
  return {slot: (v.dtype, tuple(mem[id(storage_of(r))])) for (slot, v), r in zip(outs.items(), roots)}

IMPURE = MEM | {'load', 'store', 'range', 'end'}
def assert_value(u, names):
  if not any(x.op in IMPURE for x in toposort(u, into_bodies=True)): return evaluate(u, None)
  (r,), uni = program(names, [u])
  vals, _ = execute(linearize([r], uni))
  return vals[id(r)]

def run(text, base=None):
  names, order = parse(text, base)
  for n in order:
    u = names[n]
    if u.op == 'assert' and not assert_value(u, names): raise AssertFail(f"assert failed: %{n}")

# ---------------- simplifier: bottom up greedy rewrite to a fixpoint ----------------

def bounds(u, memo):
  # conservative [lo, hi] for i32 and bool (as 0/1). None means "unknown, full range".
  if id(u) in memo: return memo[id(u)]
  full = (INT_MIN, INT_MAX) if u.dtype == 'i32' else (0, 1)
  def b(s): return bounds(s, memo)
  r = full
  if u.op == 'const' and u.dtype in ('i32', 'bool'): r = (int(u.arg), int(u.arg))
  elif u.dtype == 'bool': r = (0, 1)
  elif u.op in ('add', 'mul', 'max', 'div'):
    (a0, a1), (b0, b1) = b(u.src[0]), b(u.src[1])
    if u.op == 'add': c = [a0 + b0, a1 + b1]
    elif u.op == 'mul': c = [x * y for x in (a0, a1) for y in (b0, b1)]
    elif u.op == 'max': c = [max(a0, b0), max(a1, b1)]
    else: c = [tdiv(x, y) for x in (a0, a1) for y in (b0, b1)] if (b0 > 0 or b1 < 0) else None
    if c is not None and INT_MIN <= min(c) and max(c) <= INT_MAX: r = (min(c), max(c))   # only if no wrap
  elif u.op == 'mod' and u.src[1].op == 'const' and u.src[1].arg > 0:
    (a0, a1), m = b(u.src[0]), u.src[1].arg
    r = (0, min(m - 1, a1)) if a0 >= 0 else (-(m - 1), m - 1)
  elif u.op == 'cast' and u.src[0].dtype == 'bool': r = (0, 1)
  elif u.op == 'range': r = (0, max(b(u.src[0])[1] - 1, 0))
  elif u.op == 'where':
    (a0, a1), (b0, b1) = b(u.src[1]), b(u.src[2]); r = (min(a0, b0), max(a1, b1))
  elif u.op == 'index' and u.src[0].op == 'stack':
    bs = [b(s) for s in u.src[0].src]; r = (min(x for x, _ in bs), max(y for _, y in bs))
  memo[id(u)] = r
  return r

def substitute(body, args):
  # beta reduction: replace params reachable from body (not inside nested bodies) with args
  new = {}
  for u in toposort(body):
    if u.op == 'param': new[id(u)] = args[u.arg]
    elif u.op == 'call': new[id(u)] = UOp('call', (u.src[0],) + tuple(new[id(s)] for s in u.src[1:]), None, u.dtype, u.shape)
    else: new[id(u)] = UOp(u.op, tuple(new[id(s)] for s in u.src), u.arg, u.dtype, u.shape)
  return new[id(body)]

COMM = {'add', 'mul', 'max', 'xor'}
def isc(u, v=None): return u.op == 'const' and (v is None or (u.arg == v and isinstance(u.arg, bool) == isinstance(v, bool)))
def zero(dt): return const(False if dt == 'bool' else 0.0 if dt == 'f32' else 0, dt)

def rewrite_one(u, bm):
  op, s, dt = u.op, u.src, u.dtype
  if op == 'call': return substitute(s[0], s[1:])
  if op == 'index' and s[0].op == 'stack' and isc(s[1]) and 0 <= s[1].arg < len(s[0].src): return s[0].src[s[1].arg]
  if op in ALU and all(isc(x) for x in s):
    try: return const(alu(op, [x.dtype for x in s], [x.arg for x in s], dt), dt)
    except UIRError: return None          # keep the error in the program
  if op in COMM and isc(s[0]) and not isc(s[1]): return UOp(op, (s[1], s[0]), None, dt, ())
  if len(s) == 2: x, y = s
  if op == 'where':
    if isc(s[0]): return s[1] if s[0].arg else s[2]
    if s[1] is s[2]: return s[1]
  if op == 'cast' and s[0].dtype == dt: return s[0]
  if op == 'mul' and (isc(y, 1) or isc(y, 1.0)): return x
  if op == 'add' and dt == 'f32' and isc(y) and y.arg == 0 and math.copysign(1, y.arg) < 0: return x   # x + -0.0 is exact; x + 0.0 is not
  if op == 'max' and x is y: return x
  if op == 'cmplt' and x is y: return const(False, 'bool')
  if dt == 'i32' or (op == 'xor' and dt == 'bool'):
    if op in ('add', 'xor', 'shl') and isc(y) and y.arg in (0, False): return x
    if op == 'mul' and isc(y, 0): return y
    if op == 'xor' and x is y: return zero(dt)
    if op == 'div' and isc(y, 1): return x
    if op == 'mod' and isc(y, 1): return const(0, 'i32')
    if op in ('add', 'mul') and isc(y) and x.op == op and isc(x.src[1]):   # (x+c1)+c2: i32 is a ring, wrap is fine
      return UOp(op, (x.src[0], const(alu(op, ['i32'] * 2, [x.src[1].arg, y.arg], 'i32'), 'i32')), None, 'i32', ())
  if dt in ('i32', 'bool') and op in ('cmplt', 'max', 'mod', 'div') and s[0].dtype == 'i32':
    (a0, a1), (b0, b1) = bounds(x, bm), bounds(y, bm)
    if op == 'cmplt':
      if a1 < b0: return const(True, 'bool')
      if a0 >= b1: return const(False, 'bool')
    if op == 'max':
      if a0 >= b1: return x
      if b0 >= a1: return y
    if op == 'mod' and a0 >= 0 and b0 > 0 and a1 < b0: return x
    if op == 'div' and a0 >= 0 and b0 > 0 and a1 < b0: return const(0, 'i32')
    if op == 'div' and isc(y) and y.arg != 0 and x.op == 'mul' and x.src[1] is y and bounds(x, bm) != (INT_MIN, INT_MAX):
      return x.src[0]                     # (a*c)/c -> a, only when a*c provably didn't wrap
  return None

def simplify(root):
  while True:
    bm, new = {}, {}
    for u in toposort(root, into_bodies=True):
      srcs = tuple(new[id(x)] for x in u.src)
      n = u if srcs == u.src else UOp(u.op, srcs, u.arg, u.dtype, u.shape)
      while (r := rewrite_one(n, bm)) is not None and r is not n: n = r
      new[id(u)] = n
    if new[id(root)] is root: return root
    root = new[id(root)]

def lit(u):
  v = u.arg
  if u.dtype == 'bool': return 'true' if v else 'false'
  if u.dtype == 'i32': return str(v)
  if math.isnan(v): return 'nan'
  if math.isinf(v): return 'inf' if v > 0 else '-inf'
  return repr(v) if v != 0 or math.copysign(1, v) > 0 else '-0.0'

def render(root, name='out'):
  lines, names = [], {}
  for u in toposort(root, into_bodies=True):
    if u.op == 'const': names[id(u)] = lit(u); continue
    nm = f"%{name}" if u is root else f"%t{len(lines)}"
    if u.op == 'param': rhs = f"param {u.arg} dtype={u.dtype}" + (f" shape=[{u.shape[0]}]" if u.shape else "")
    else:
      rhs = ' '.join([u.op] + [names[id(s)] for s in u.src]) + (f" dtype={u.dtype}" if u.op in ('cast', 'bitcast') else '')
    names[id(u)] = nm; lines.append(f"{nm} = {rhs}")
  if root.op == 'const': lines.append(f"%{name} = const {lit(root)}")
  return '\n'.join(lines) + '\n'

# ---------------- render C (week 2) ----------------

CT = {'f32': 'float', 'i32': 'int32_t', 'bool': 'bool'}
def c_lit(v, dt):
  if dt == 'bool': return 'true' if v else 'false'
  if dt == 'i32': return '(-2147483647 - 1)' if v == INT_MIN else str(v)
  if math.isnan(v): return 'NAN'
  if math.isinf(v): return 'INFINITY' if v > 0 else '(-INFINITY)'
  return float.hex(v) + 'f'                          # hex floats are exact

def inline_calls(roots):
  memo = {}
  def rb(u):
    if id(u) in memo: return memo[id(u)]
    if u.op == 'call': r = rb(substitute(u.src[0], tuple(rb(a) for a in u.src[1:])))
    else: r = u if not u.src else UOp(u.op, tuple(rb(x) for x in u.src), u.arg, u.dtype, u.shape)
    memo[id(u)] = r; return r
  return [rb(r) for r in roots]

C_HELPERS = """static inline float f32_max(float a, float b) {
  if (isnan(a) || isnan(b)) return NAN;
  if (a == 0.0f && b == 0.0f) return signbit(a) ? b : a;   /* max(-0.0, 0.0) is +0.0 either way */
  return a > b ? a : b;
}
static inline int32_t f32_bits(float x) { int32_t i; if (isnan(x)) return 0x7fc00000; memcpy(&i, &x, 4); return i; }
static inline float bits_f32(int32_t i) { float x; memcpy(&x, &i, 4); return x; }
"""

def needs_loops(names):
  # week 3+ programs: hand-written ranges, or week 4 shape ops that rangeify into loops
  # a big rank-1 value (a 4096-element copy, say) must be a loop too, or the C blows past the size limit
  return any(u.op == 'range' or u.op in SHAPE_OPS or (u.op in ALU and u.shape) or len(u.shape) >= 2
             or (len(u.shape) == 1 and u.shape[0] > 32 and u.op not in MEM) for u in all_nodes(names))

def rangeify(nodes):
  """Remove shapes from every op: each shaped value is asked for its element at an index tuple (ranges or
  constants). Movement ops become index arithmetic, reduce an accumulator loop over its leading axes,
  a rank-1 store a store loop, stage a temp buffer filled once. Without stage, a value used twice is
  recomputed at each use (fusion)."""
  low_memo, el_memo = {}, {}
  def c(v): return const(v, 'i32')
  def A(op, *srcs, dt='i32'): return UOp(op, srcs, None, dt, ())
  def add(a, b):                                 # index math: fold constants so the C stays readable
    if a.op == 'const' and b.op == 'const': return c(wrap(a.arg + b.arg))
    if a.op == 'const' and a.arg == 0: return b
    if b.op == 'const' and b.arg == 0: return a
    return A('add', a, b)
  def mul(a, k):
    if a.op == 'const': return c(wrap(a.arg * k))
    return a if k == 1 else A('mul', a, c(k))
  def sv(view, i): return UOp('shrink', (view, i), None, view.dtype, ())     # scalar view, in range by construction
  def rng(n, tag): return UOp('range', (c(n),), ('range', f"_{tag}"), 'i32', ())
  def end(st, r): return UOp('end', (st, r), None, 'void', ())
  def store(v, x): return UOp('store', (v, x), None, 'void', ())
  def after(m, e): return UOp('after', (m, e), None, m.dtype, m.shape)
  def load(v, dt): return UOp('load', (v,), None, dt, ())
  def flat_of(idx, shape):                       # row-major flat index of idx in shape
    f = c(0)
    for i, d in zip(idx, shape): f = add(mul(f, d), i)
    return f
  def unflat(f, shape):                          # (f div stride) mod size, per axis
    out, stride = [], prod(shape)
    for d in shape:
      stride //= d
      q = f if stride == 1 else (c(f.arg // stride) if f.op == 'const' else A('div', f, c(stride)))
      out.append(c(0) if d == 1 else (c(q.arg % d) if q.op == 'const' else A('mod', q, c(d))))
    return tuple(out)
  def tag(u, idx): return f"{id(u)}_" + '_'.join(str(id(i)) for i in idx)
  def low(u):
    if id(u) in low_memo: return low_memo[id(u)]
    op = u.op
    if not u.shape and (op in SHAPE_OPS or (op == 'index' and u.src[0].op != 'stack')): out = el(u, ())
    elif op == 'store' and u.src[1].shape:
      view, val = u.src; r = rng(val.shape[0], f"st{id(u)}")
      # the value is computed from the old contents. If it reads the memory this loop overwrites, a later
      # iteration would see an earlier one's store: materialize the value first, then copy it in
      if any(n.op == 'load' and storage_of(n.src[0]) is storage_of(view) for n in toposort(val)):
        val = UOp('stage', (val,), None, val.dtype, val.shape)
      out = end(store(sv(low(view), r), el(val, (r,))), r)
    else: out = u if not u.src else UOp(op, tuple(low(x) for x in u.src), u.arg, u.dtype, u.shape)
    low_memo[id(u)] = out; return out
  def el(u, idx):
    if not u.shape and not (u.op in SHAPE_OPS or u.op == 'index'): return low(u)
    k = (id(u),) + tuple(id(i) for i in idx)
    if k in el_memo: return el_memo[k]
    op, xs = u.op, (u.src[0].shape if u.src else ())
    if op in ALU: out = UOp(op, tuple(el(x, idx) for x in u.src), None, u.dtype, ())
    elif op == 'expand': out = low(u.src[0]) if not xs else el(u.src[0], tuple(c(0) if a == 1 and b != 1 else i for a, b, i in zip(xs, u.shape, idx)))
    elif op == 'reshape': out = el(u.src[0], idx if xs == u.shape else unflat(flat_of(idx, u.shape), xs))
    elif op == 'permute':
      s_ = [None] * len(idx)
      for kk, p_ in enumerate(u.arg): s_[p_] = idx[kk]
      out = el(u.src[0], tuple(s_))
    elif op == 'pad':
      pads, valid, src_idx = u.arg, None, []
      for kk, (i, d) in enumerate(zip(idx, xs)):
        l, r = pads[2 * kk], pads[2 * kk + 1]
        if l == 0 and r == 0: src_idx.append(i); continue
        sh = add(i, c(-l)) if l else i
        lo = A('max', sh, c(0)) if l else sh                                   # clamp into [0, d-1] so reads stay in range
        src_idx.append(A('mul', A('max', A('mul', lo, c(-1)), c(-(d - 1))), c(-1)) if r else lo)
        ok = A('where', A('cmplt', c(l - 1), i, dt='bool'), A('cmplt', i, c(l + d), dt='bool'), const(False, 'bool'), dt='bool')
        valid = ok if valid is None else A('where', valid, ok, const(False, 'bool'), dt='bool')
      inner = el(u.src[0], tuple(src_idx))
      out = inner if valid is None else A('where', valid, inner, const(ZERO[u.dtype], u.dtype), dt=u.dtype)
    elif op == 'vshrink': out = el(u.src[0], tuple(add(low(o), i) for i, o in zip(idx, u.src[1:])))
    elif op == 'stage':
      x, n = u.src[0], prod(u.shape)
      tmp = UOp('alloc', (), ('alloc', n, f"_stage{id(u)}"), u.dtype, (n,))
      r = rng(n, f"stg{id(u)}")
      filled = after(tmp, end(store(sv(tmp, r), el(x, unflat(r, u.shape))), r))
      out = load(sv(filled, flat_of(idx, u.shape)), u.dtype)              # filled once, read at idx
    elif op == 'reduce':
      (rop, m), x = u.arg, u.src[0]
      lead, T, t = xs[:m], prod(xs[:m]), tag(u, idx)
      acc = UOp('alloc', (), ('alloc', 1, f"_acc{t}"), u.dtype, (1,))
      acc1 = after(acc, store(sv(acc, c(0)), el(x, (c(0),) * m + idx)))  # start from the first element
      r = rng(T - 1, f"red{t}")
      xe = el(x, unflat(A('add', r, c(1)), lead) + idx)
      # an element that doesn't depend on r (an expanded axis, read at 0) must still be added T - 1 times:
      # tie the accumulator's address to r, or the add is hoisted out of an empty loop
      a1 = sv(acc1, c(0) if r in opens(xe) else A('mul', r, c(0)))
      nxt = UOp(rop, (load(a1, u.dtype), xe), None, u.dtype, ())
      out = load(sv(after(acc1, end(store(a1, nxt), r)), c(0)), u.dtype)  # fold the rest in row-major order
    elif op == 'stack':
      items, rest = u.src, idx[1:]
      if not items[0].shape: out = UOp('index', (low(u), idx[0]), None, u.dtype, ())   # a C array of scalars
      else:
        out = el(items[-1], rest)
        for j in reversed(range(len(items) - 1)):
          out = A('where', A('cmplt', idx[0], c(j + 1), dt='bool'), el(items[j], rest), out, dt=u.dtype)
    elif op == 'index': out = el(u.src[0], tuple(low(j) for j in u.src[1:]) + idx)
    elif op == 'load': out = load(sv(low(u.src[0]), idx[0]), u.dtype)
    else: raise UIRError(f"rangeify: can't take an element of {op}")
    el_memo[k] = out; return out
  return [low(n) for n in nodes]

def render_c(names):
  outs = final_versions(names)
  roots, uni = program(names, list(outs.values()))
  if needs_loops(names):                         # week 4: shapes become loops; week 2 programs stay loopless
    low = rangeify(roots + uni)                  # asserts stay in the universe: they decide where loads run
    roots, uni = low[:len(roots)], low[len(roots):]
  low = lower_math(roots + uni)                  # week 6: exp2, log2, sqrt, sin become their bodies
  roots, uni = low[:len(roots)], low[len(roots):]
  block = linearize(roots, uni)
  ptr, name, lines = {}, {}, []
  for (slot, v), r in zip(outs.items(), roots): ptr[id(storage_of(r))] = f"b{slot}"
  counter = [0]
  def ex(u): return c_lit(u.arg, u.dtype) if u.op == 'const' else name[id(u)]
  def view(u):
    if u.op != 'shrink': return ptr[id(storage_of(u))], '0'
    p, o = view(u.src[0]); off = ex(u.src[1])
    return p, (off if o == '0' else f"{o} + {off}")
  def emit(items, depth):
    pad = '  ' * depth
    for it in items:
      if isinstance(it, tuple):
        _, e, r, body = it
        rv = f"r{counter[0]}"; counter[0] += 1; name[id(r)] = rv
        lines.append(f"{pad}for (int32_t {rv} = 0; {rv} < {ex(r.src[0])}; {rv}++) {{")
        emit(body, depth + 1); lines.append(f"{pad}}}"); continue
      u = it; op = u.op; i = counter[0]; counter[0] += 1
      v, t = f"v{i}", CT.get(u.dtype)
      if op in ('const', 'after', 'shrink', 'buffer', 'end', 'range', 'assert'): continue
      if op == 'alloc': ptr[id(u)] = f"a{i}"; lines.append(f"{pad}{t} a{i}[{u.arg[1]}] = {{0}};"); continue
      if op == 'load':
        p, o = view(u.src[0])
        if u.shape: lines.append(f"{pad}{t} {v}[{u.shape[0]}] = {{" + ', '.join(f"{p}[{o} + {j}]" for j in range(u.shape[0])) + "};")
        else: lines.append(f"{pad}{t} {v} = {p}[{o}];")
        name[id(u)] = v; continue
      if op == 'store':
        p, o = view(u.src[0]); x = ex(u.src[1])
        if u.src[0].shape: lines.extend(f"{pad}{p}[{o} + {j}] = {x}[{j}];" for j in range(u.src[0].shape[0]))
        else: lines.append(f"{pad}{p}[{o}] = {x};")
        continue
      a = [ex(x) for x in u.src]
      if op == 'stack': lines.append(f"{pad}{t} {v}[{len(a)}] = {{{', '.join(a)}}};"); name[id(u)] = v; continue
      if op == 'index': e = f"{a[0]}[{a[1]}]"
      elif op == 'detach': e = a[0]
      elif op == 'bitcast': e = a[0] if u.src[0].dtype == u.dtype else f"f32_bits({a[0]})" if u.dtype == 'i32' else f"bits_f32({a[0]})"
      elif op == 'where': e = f"({a[0]} ? {a[1]} : {a[2]})"
      elif op == 'cast':
        fr = u.src[0].dtype
        e = a[0] if fr == u.dtype else f"({a[0]} != 0)" if u.dtype == 'bool' else f"(({t}){a[0]})"
      elif op == 'recip': e = f"(1.0f / {a[0]})"
      elif op == 'cmplt': e = f"({a[0]} < {a[1]})"
      elif op == 'xor': e = f"({a[0]} != {a[1]})" if u.dtype == 'bool' else f"({a[0]} ^ {a[1]})"
      elif op == 'max': e = f"f32_max({a[0]}, {a[1]})" if u.dtype == 'f32' else f"({a[0]} > {a[1]} ? {a[0]} : {a[1]})"
      elif op in ('add', 'mul') and u.dtype == 'f32': e = f"({a[0]} {'+' if op == 'add' else '*'} {a[1]})"
      elif op in ('add', 'mul', 'shl'):              # wrap through uint32_t: signed overflow is UB in C
        e = f"(int32_t)((uint32_t){a[0]} {dict(add='+', mul='*', shl='<<')[op]} (uint32_t){a[1]})"
      elif op in ('div', 'mod') and u.src[1].op == 'const' and u.src[1].arg not in (0, -1): e = f"({a[0]} {'/' if op == 'div' else '%'} {a[1]})"   # a constant divisor can't be -1
      elif op == 'div': e = f"({a[1]} == -1 ? (int32_t)(0u - (uint32_t){a[0]}) : {a[0]} / {a[1]})"   # INT_MIN / -1 is UB
      elif op == 'mod': e = f"({a[1]} == -1 ? 0 : {a[0]} % {a[1]})"
      else: raise UIRError(f"render: can't render {op} here")
      lines.append(f"{pad}{t} {v} = {e};"); name[id(u)] = v
  emit(block, 1)
  params = ', '.join(f"{CT[v.dtype]} *b{slot}" for slot, v in outs.items()) or 'void'
  return ("#include <stdint.h>\n#include <stdbool.h>\n#include <string.h>\n#include <math.h>\n\n" + C_HELPERS +
          f"\nvoid kernel({params}) {{\n" + ''.join(f"{l}\n" for l in lines) + "}\n")

def count_ops(root): return sum(u.op not in ('const', 'param') for u in toposort(root, into_bodies=True))

def read_text(path):
  b = open(path, 'rb').read()
  if b.startswith(b'\xff\xfe') or b.startswith(b'\xfe\xff'): return b.decode('utf-16')   # PowerShell 5.1 ">" writes UTF-16
  return b.decode('utf-8-sig')

def main(argv):
  if len(argv) != 3 or argv[1] not in ('run', 'simplify', 'render'):
    print("usage: uirc.py run|simplify|render FILE", file=sys.stderr); return 2
  try:
    text, base = read_text(argv[2]), os.path.dirname(os.path.abspath(argv[2]))
    if argv[1] == 'run': run(text, base); return 0
    if argv[1] == 'render': sys.stdout.write(render_c(parse(text, base)[0])); return 0
    names, _ = parse(text, base)
    if 'out' not in names: raise UIRError("simplify needs %out")
    sys.stdout.write(render(simplify(names['out']))); return 0
  except AssertFail as e: print(e, file=sys.stderr); return 1
  except UIRError as e: print(f"invalid: {e}", file=sys.stderr); return 2
  except (UnicodeDecodeError, OSError) as e: print(f"invalid: can't read {argv[2]}: {e}", file=sys.stderr); return 2
  except RecursionError: print("invalid: nesting too deep", file=sys.stderr); return 2

def run_main():
  # nested calls recurse; give them room
  sys.setrecursionlimit(100000); threading.stack_size(128 * 1024 * 1024)
  rc = []; t = threading.Thread(target=lambda: rc.append(main(sys.argv))); t.start(); t.join()
  sys.exit(rc[0] if rc else 2)

if __name__ == '__main__': run_main()
