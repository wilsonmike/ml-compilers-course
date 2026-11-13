#!/usr/bin/env python3
"""Course test runner. Run from the course repo root.

  python tools/test.py --compiler PATH/TO/your.exe --week 1 [-k substr] [-v] [--jobs N]
  python tools/test.py --check-tests DIR           # check YOUR tests' headers against the oracle
  python tools/test.py --self-check --week 1       # check the course suite against the oracle

Your compiler is run as `COMPILER run FILE`, `COMPILER simplify FILE` (spec/uir-week1.md) and, from
week 2, `COMPILER render FILE` (spec/uir-week2.md).
The oracle (_reference/) is imported to grade simplify output. Running it is fine; reading it spoils the course.
"""
import sys, os, re, glob, math, random, shlex, argparse, subprocess, importlib.util, itertools, tempfile, threading, shutil, struct
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location('oracle', os.path.join(ROOT, '_reference', 'uirc.py'))
O = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(O)
ORACLE = [sys.executable, os.path.join(ROOT, '_reference', 'uirc.py')]
TIMEOUT = 10

def headers(text):
  h = dict(re.findall(r"^#\s*(expect|simplify|time|max_bytes|speed):\s*(.+?)\s*$", text, re.M))
  if 'simplify' in h: h['max_ops'] = int(re.search(r"max_ops=(\d+)", h['simplify']).group(1))
  if re.search(r"^#\s*render\s*$", text, re.M): h['render'] = True
  if re.search(r"^#\s*cuda\s*$", text, re.M): h['cuda'] = True       # week 8: render-cuda, checked on a GPU or the emulator
  if (m := re.search(r"^#\s*cuda speed:\s*([0-9.]+)\s*$", text, re.M)): h['cuda'] = True; h['cuda_speed'] = float(m.group(1))
  if re.search(r"^#\s*cuda:\s*invalid\s*$", text, re.M): h['cuda'] = True; h['cuda_invalid'] = True   # render-cuda must exit 2
  if 'speed' in h: h['render'] = True
  if (m := re.search(r"^#\s*render check:\s*slot\s+(\d+)\s*>=\s*(-?[0-9.]+)\s*$", text, re.M)):   # week 6: a threshold, not bits
    h['render'] = True; h['check'] = (int(m.group(1)), float(m.group(2)))
  return h

def url_files(text):
  # relative url= paths a program reads: the grader copies them next to the neutral test file
  return [u for u in re.findall(r"\burl=([^ \t\r\n#]+)", text) if not u.startswith('https://')]

def oracle_run(text, base=None):
  try: O.run(text, base); return 'pass', None
  except O.AssertFail as e: return 'assert_fail', str(e)
  except O.UIRError as e: return 'invalid', str(e)

def call(cmd, sub, text, base=None, timeout=TIMEOUT):
  # tests run under a neutral file name, so a compiler can't read the expected outcome off "err_*.uir"
  with tempfile.TemporaryDirectory() as d:
    path = os.path.join(d, 'case.uir')
    open(path, 'w', encoding='utf-8', newline='\n').write(text)
    for u in url_files(text):                       # week 6: data files travel with the test
      parts = u.split('/'); src = os.path.join(base or ROOT, *parts)
      if '..' not in parts and os.path.isfile(src):
        dst = os.path.join(d, *parts); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copyfile(src, dst)
    try:
      p = subprocess.run(cmd + [sub, path], capture_output=True, timeout=timeout)
      dec = lambda b: b.decode('utf-8', 'replace').replace(chr(13) + chr(10), chr(10))   # Windows CRLF
      return p.returncode, dec(p.stdout), dec(p.stderr)
    except subprocess.TimeoutExpired: return 'timeout', '', f'timed out after {timeout:g}s'
    except OSError as e: return 'error', '', str(e)

CODE = {'pass': 0, 'assert_fail': 1, 'invalid': 2}
ASSERT_LINE = re.compile(r"^assert failed: %([A-Za-z0-9_]+)[ \t]*$", re.M | re.A)

def grade_run(cmd, text, base=None):
  want, msg = oracle_run(text, base)
  rc, _, err = call(cmd, 'run', text, base)
  tail = f"\n    stderr: {err.strip()[:300]}" if err.strip() else ""
  if rc != CODE[want]: return f"expected exit {CODE[want]} ({want}), got {rc}" + (f"\n    oracle: {msg}" if msg else "") + tail
  if want == 'invalid' and not re.search(r"^invalid:", err, re.M):
    return "exit 2 is right, but stderr needs a line starting 'invalid:' (an uncaught exception isn't a diagnosis)" + tail
  if want == 'assert_fail':
    named = ASSERT_LINE.findall(err)
    if named != [msg.split('%', 1)[1]]: return f"exit 1 is right, but stderr must have exactly one line '{msg}'" + tail
  return None

# ---- simplify grading: ops counted on your text, then equivalence on edge-case inputs ----

def exact(xs): return [O.f32(x) for x in xs]
EDGE = {'i32': [0, 1, -1, 2, -2, 7, 8, -8, 255, 65536, 2**30, -2**30, O.INT_MAX, O.INT_MIN, O.INT_MAX - 1, O.INT_MIN + 1],
        # every value is a real f32: the largest finite, the smallest subnormal, signed zeros, infinities, nan
        'f32': exact([0.0, -0.0, 1.0, -1.0, 0.5, 3.0, 1e8, -1e8, 1.401298464324817e-45, -1.401298464324817e-45,
                      1.1754943508222875e-38, 3.4028234663852886e38, -3.4028234663852886e38, math.inf, -math.inf, math.nan]),
        'bool': [False, True]}

def rand_value(dt, rng):
  if dt == 'i32': return rng.randint(O.INT_MIN, O.INT_MAX)
  r = rng.random()
  if r < .06: return math.nan
  if r < .12: return rng.choice([math.inf, -math.inf])
  if r < .25: return O.f32(rng.choice([-1, 1]) * rng.uniform(0, 1.2e-38))      # subnormals and tiny normals
  return O.f32(rng.uniform(-1e6, 1e6) * rng.choice([1, 1e-30, 1e30]))

def cases(slots, rng):
  # every slot sees every edge value: full cross product for <= 2 slots, a rotation for more
  pools = [EDGE[dt] + ([rand_value(dt, rng) for _ in range(8)] if dt != 'bool' else []) for dt, _ in slots]
  if len(pools) <= 2: return [list(c) for c in itertools.product(*[range(len(p)) for p in pools])], pools
  rows = []
  for s, p in enumerate(pools):
    for k in range(len(p)):
      rows.append([k if t == s else (k * 7 + 3 * t + s) % len(pools[t]) for t in range(len(pools))])
  return rows, pools

def build_arg(dt, shape, pool, k):
  if not shape: return O.const(pool[k], dt)
  return O.build('stack', [O.const(pool[(k + j) % len(pool)], dt) for j in range(shape[0])], {})

def same(a, b):
  # f32 by bit pattern (so 0.0 and -0.0 differ), any NaN equals any NaN
  if isinstance(a, tuple): return isinstance(b, tuple) and len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
  if isinstance(a, float): return isinstance(b, float) and ((math.isnan(a) and math.isnan(b)) or O.fbits(a) == O.fbits(b))
  return a == b

def text_ops(out):
  # ops as written: every reachable "%name = op" statement except const/param. Duplicates count.
  defs = {}
  for line in out.split('\n'):
    m = re.match(r"[ \t]*%([A-Za-z0-9_]+)[ \t]*=[ \t]*([a-z_][a-z0-9_]*)(.*)", line.split('#', 1)[0], re.A)
    if m: defs[m.group(1)] = (m.group(2), re.findall(r"%([A-Za-z0-9_]+)", m.group(3), re.A))
  seen, todo = set(), ['out']
  while todo:
    n = todo.pop()
    if n in seen or n not in defs: continue
    seen.add(n); todo.extend(defs[n][1])
  return sum(defs[n][0] not in ('const', 'param') for n in seen)

def grade_simplify(cmd, text, max_ops):
  rc, out, err = call(cmd, 'simplify', text)
  if rc != 0: return f"simplify exited {rc}\n    stderr: {err.strip()[:300]}"
  try: mine = O.parse(out)[0]
  except O.UIRError as e: return f"your output is not valid .uir: {e}\n    output:\n{indent(out)}"
  if 'out' not in mine: return f"your output doesn't define %out\n    output:\n{indent(out)}"
  orig, new = O.parse(text)[0]['out'], mine['out']
  if (orig.dtype, orig.shape) != (new.dtype, new.shape): return f"%out changed type: {orig.dtype}{list(orig.shape)} -> {new.dtype}{list(new.shape)}"
  n = text_ops(out)
  if n > max_ops: return f"{n} ops in your output, the target is <= {max_ops}\n    output:\n{indent(out)}"
  params = O.free_params(orig)
  slots = [(params[s].dtype, params[s].shape) if s in params else ('i32', ()) for s in range(max(params) + 1)] if params else []
  rows, pools = cases(slots, random.Random(411))
  for row in rows or [[]]:
    args = [build_arg(dt, sh, pools[s], row[s]) for s, (dt, sh) in enumerate(slots)]
    try: want = O.evaluate(O.build('call', [orig] + args, {}), None)
    except O.UIRError: continue                     # original errors here: any answer is fine
    try: c = O.build('call', [new] + args, {})
    except O.UIRError as e: return f"your %out's params don't match the original's: {e}\n    output:\n{indent(out)}"
    try: got = O.evaluate(c, None)
    except O.UIRError as e: return f"your %out errors where the original doesn't: {e}\n    args: {show(args)}"
    if not same(want, got): return f"wrong value: original gives {want!r}, yours gives {got!r}\n    args: {show(args)}\n    output:\n{indent(out)}"
  return None

# ---- render grading (week 2): compile your C with a harness, run it, compare the buffers ----

CC = next((shutil.which(c) for c in ('clang', 'gcc') if shutil.which(c)), None)
CFLAGS = ['-std=c11', '-O2', '-ffp-contract=off', '-fsanitize=undefined', '-fsanitize-trap=undefined']
CT = {'f32': 'float', 'i32': 'int32_t', 'bool': 'bool', 'i8': 'int8_t'}

def strip_c(src):
  # drop comments and string/char literals before looking for loops
  return re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', ' ', src, flags=re.S)

THREADS = max(1, min(64, os.cpu_count() or 1))
PARALLEL_FOR = f"\n#ifndef UIR_THREADS\n#define UIR_THREADS {THREADS}\n#endif" + r"""
#include <pthread.h>
/* week 7: the harness runs thread loops. Iterations are split into one contiguous chunk per thread. */
typedef struct { int32_t lo, hi; void (*body)(int32_t, void *); void *ctx; } uir_chunk;
static void *uir_run(void *p) { uir_chunk *c = p; for (int32_t i = c->lo; i < c->hi; i++) c->body(i, c->ctx); return 0; }
void uir_parallel_for(int32_t n, void (*body)(int32_t, void *), void *ctx) {
  int t = UIR_THREADS < n ? UIR_THREADS : n; if (t < 1) t = 1;
  pthread_t th[64]; uir_chunk ch[64];
  for (int k = 0; k < t; k++) {
    ch[k] = (uir_chunk){ (int32_t)((int64_t)n * k / t), (int32_t)((int64_t)n * (k + 1) / t), body, ctx };
    if (k) pthread_create(&th[k], 0, uir_run, &ch[k]);
  }
  uir_run(&ch[0]);
  for (int k = 1; k < t; k++) pthread_join(th[k], 0);
}
"""

def harness(names, timed=False):
  outs = O.final_versions(names)
  bufs = {u.arg[1]: u for u in O.all_nodes(names) if u.op == 'buffer'}
  lines = ['#include <stdio.h>', '#include <stdint.h>', '#include <stdbool.h>', '#include <string.h>',
           'void kernel(' + (', '.join(f"{CT[bufs[k].dtype]} *b{k}" for k in outs) or 'void') + ');', 'int main(void) {']
  for k, b in bufs.items():
    n, data = b.arg[2], b.arg[3]
    if isinstance(data, O.Blob):                     # week 6 url=: read the verified file at run time
      lines.append(f"  static {CT[b.dtype]} b{k}[{n}];")
      lines.append(f'  {{ FILE *f = fopen("{data.path.replace(chr(92), "/")}", "rb"); if (!f || fread(b{k}, 1, sizeof b{k}, f) != sizeof b{k}) return 3; fclose(f); }}')
    elif b.dtype == 'f32':
      lines.append(f"  static const uint32_t i{k}[{n}] = {{{', '.join(hex(struct.unpack('<I', O.fbits(x))[0]) for x in data)}}};")
      lines.append(f"  static float b{k}[{n}]; memcpy(b{k}, i{k}, sizeof b{k});")
    else: lines.append(f"  static {CT[b.dtype]} b{k}[{n}] = {{{', '.join(str(int(x)) for x in data)}}};")
  call_k = '  kernel(' + ', '.join(f"b{k}" for k in outs) + ');'
  if timed:                                       # week 7: time the kernel alone, with a monotonic clock
    lines.insert(0, '#include <time.h>')
    lines.append('  struct timespec t0_, t1_; clock_gettime(CLOCK_MONOTONIC, &t0_);')
    lines.append(call_k)
    lines.append('  clock_gettime(CLOCK_MONOTONIC, &t1_); fprintf(stderr, "kernel %.9f\\n", (t1_.tv_sec - t0_.tv_sec) + (t1_.tv_nsec - t0_.tv_nsec) * 1e-9);')
  else: lines.append(call_k)
  for k, b in bufs.items():
    if isinstance(b.arg[3], O.Blob) and outs[k] is b: continue          # an input file nothing stores to
    if b.dtype == 'f32': lines.append(f"  for (int i = 0; i < {b.arg[2]}; i++) {{ uint32_t u; memcpy(&u, &b{k}[i], 4); printf(\"{k} %08x\\n\", u); }}")
    else: lines.append(f"  for (int i = 0; i < {b.arg[2]}; i++) printf(\"{k} %d\\n\", (int)b{k}[i]);")
  return '\n'.join(lines + ['  return 0;', '}']) + '\n'

def grade_render(cmd, text, base=None, h=None):
  if not CC: return "no C compiler found (clang or gcc) to build your rendered C"
  h = h or {}
  limit = float(h.get('time', TIMEOUT))
  rc, out, err = call(cmd, 'render', text, base, limit)
  if rc != 0: return f"render exited {rc}\n    stderr: {err.strip()[:300]}"
  names = O.parse(text, base)[0]
  if 'speed' in h: return grade_speed(out, names, float(h['speed']), limit)
  looped = O.needs_loops(names)                 # weeks 3-4: ranges, or shape ops that rangeify into loops
  cap = int(h.get('max_bytes', 20000))
  if len(out.encode()) > cap: return f"rendered C is {len(out.encode())} bytes; the limit is {cap} (rank-1 values must become loops, not unrolled code)"
  if re.search(r'\b(while|goto|do)\b' if looped else r'\b(for|while|goto|do)\b', strip_c(out)):
    return ("render may only use for loops" if looped else "render must produce loopless C (found for/while/do/goto)") + "\n    output:\n" + indent(out)
  outs = O.final_versions(names)
  skip = {k for k, v in outs.items() if v.op == 'buffer' and isinstance(v.arg[3], O.Blob)}   # unchanged input files
  want = {} if 'check' in h else {k: v for k, v in O.final_buffers(names).items() if k not in skip}
  with tempfile.TemporaryDirectory() as d:
    k, hp, exe = os.path.join(d, 'kernel.c'), os.path.join(d, 'harness.c'), os.path.join(d, 'a.exe' if os.name == 'nt' else 'a.out')
    open(k, 'w', encoding='utf-8').write(out); open(hp, 'w', encoding='utf-8').write(harness(names) + (PARALLEL_FOR if 'uir_parallel_for' in out else ''))
    flags = CFLAGS if 'clang' in os.path.basename(CC) else CFLAGS[:-1] + ['-fsanitize-undefined-trap-on-error']
    c = subprocess.run([CC, *flags, k, hp, '-o', exe, '-lm'] + (['-lpthread'] if 'uir_parallel_for' in out else []), capture_output=True, timeout=max(60, limit))
    if c.returncode != 0: return "your C doesn't compile:\n" + indent(c.stderr.decode('utf-8', 'replace').replace(d + os.sep, ''))
    try: r = subprocess.run([exe], capture_output=True, timeout=limit)
    except subprocess.TimeoutExpired:
      if looped: return f"your kernel didn't finish in {limit:g}s"
      return (f"your kernel didn't finish in {limit:g}s. With no loops allowed, the usual cause is undefined behavior: "
                                               "on Windows a plain INT_MIN / -1 (or % -1) hangs instead of trapping. Guard div and mod.")
    if r.returncode == 3 and skip: return "the harness couldn't read a url= data file"
    if r.returncode != 0: return f"your kernel crashed (exit {r.returncode}). With -fsanitize-trap that usually means undefined behavior: signed overflow, INT_MIN / -1, a bad shift, or an out-of-bounds access."
    got, vals = {}, r.stdout.decode().split('\n')
    for line in vals:
      if not line.strip(): continue
      slot, v = line.split(); got.setdefault(int(slot), []).append(v)
  if 'check' in h:
    slot, lo = h['check']; g = got.get(slot, [])
    if not g: return f"buffer {slot}: the harness read nothing"
    v = struct.unpack('<f', struct.pack('<I', int(g[0], 16)))[0] if outs[slot].dtype == 'f32' else int(g[0])
    return None if v >= lo else f"buffer {slot}[0] is {v:g}, the target is >= {lo:g}"
  for slot, (dt, data) in want.items():
    g = got.get(slot, [])
    if len(g) != len(data): return f"buffer {slot}: harness read {len(g)} values, expected {len(data)}"
    for i, (x, y) in enumerate(zip(data, g)):
      if dt == 'f32':
        gb = struct.pack('<I', int(y, 16)); gx = struct.unpack('<f', gb)[0]
        ok = (math.isnan(x) and math.isnan(gx)) or O.fbits(x) == gb
      else: ok = int(y) == int(x)
      if not ok: return f"buffer {slot}[{i}]: expected {x!r}, your kernel left {struct.unpack('<f', struct.pack('<I', int(y, 16)))[0] if dt == 'f32' else y}"
  return None

def build_timed(d, tag, c_src, names):
  """Compile a kernel with the timing harness at -O2, without sanitizers (they slow code down). Returns exe or error."""
  k, hp, exe = os.path.join(d, f'{tag}.c'), os.path.join(d, f'{tag}_h.c'), os.path.join(d, tag + ('.exe' if os.name == 'nt' else ''))
  open(k, 'w', encoding='utf-8').write(c_src)
  open(hp, 'w', encoding='utf-8').write(harness(names, timed=True) + (PARALLEL_FOR if 'uir_parallel_for' in c_src else ''))
  c = subprocess.run([CC, '-std=c11', '-O2', '-ffp-contract=off', f'-DUIR_THREADS={THREADS}', k, hp, '-o', exe, '-lm', '-lpthread'], capture_output=True, timeout=120)
  return exe if c.returncode == 0 else ("doesn't compile:\n" + indent(c.stderr.decode('utf-8', 'replace').replace(d + os.sep, '')))

def grade_speed(out, names, speed, limit):
  """# speed: X. Your kernel must give the reference kernel's bits and run in at most (reference time) / X,
  both built the same way on this machine. Best of 3 runs each, interleaved, so load spikes hit both."""
  if not CC: return "no C compiler found (clang or gcc) to build your rendered C"
  ref = O.render_c(names)
  with tempfile.TemporaryDirectory() as d:
    mine = build_timed(d, 'mine', out, names)
    if not os.path.exists(mine): return "your C " + mine
    theirs = build_timed(d, 'ref', ref, names)
    if not os.path.exists(theirs): return "grader error: the reference kernel " + theirs
    best = {'mine': 1e9, 'ref': 1e9}; outputs = {}
    for _ in range(3):
      for tag, exe in (('mine', mine), ('ref', theirs)):
        try: r = subprocess.run([exe], capture_output=True, timeout=limit)
        except subprocess.TimeoutExpired: return f"{'your' if tag == 'mine' else 'the reference'} kernel didn't finish in {limit:g}s"
        if r.returncode != 0: return f"{'your' if tag == 'mine' else 'the reference'} kernel crashed (exit {r.returncode})"
        outputs[tag] = r.stdout
        best[tag] = min(best[tag], float(re.search(rb"kernel ([0-9.e-]+)", r.stderr).group(1)))
    if outputs['mine'] != outputs['ref']:
      a, b = outputs['mine'].decode().split('\n'), outputs['ref'].decode().split('\n')
      i = next(i for i, (x, y) in enumerate(zip(a + [''], b + [''])) if x != y)
      return f"wrong result: line {i} of the buffers is {a[i] if i < len(a) else '(missing)'!r}, the reference gives {b[i] if i < len(b) else '(missing)'!r}"
    threaded = 'uir_parallel_for' in ref
    if threaded and THREADS < 4: return None    # too few cores to time thread loops fairly: correctness only
    if best['mine'] > best['ref'] / speed:
      return f"too slow: your kernel took {best['mine'] * 1e3:.1f} ms, the target is at most {best['ref'] / speed * 1e3:.1f} ms (the reference took {best['ref'] * 1e3:.1f} ms)"
  return None

# ---- week 8: render-cuda. Real CUDA when it's there (local nvcc, or Docker with --cuda-docker), else an emulator ----
CXX = next((shutil.which(c) for c in ('clang++', 'g++') if shutil.which(c)), None)
NVCC = shutil.which('nvcc')
CUDA_DOCKER = os.environ.get('UIR_CUDA_DOCKER', '')    # e.g. nvidia/cuda:12.6.3-devel-ubuntu22.04, set by --cuda-docker
EMULATOR = r"""// The grader's CUDA emulator: compiles your .cu as C++. Blocks run one after another; the threads of a block
// are real threads, so a missing __syncthreads() shows up as a race, not as luck.
#include <pthread.h>
#include <functional>
#include <type_traits>
#include <vector>
#define __global__
#define __device__
#define __shared__ static
#define __restrict__
#define __align__(n) __attribute__((aligned(n)))
struct uir_dim { int x; };
static thread_local uir_dim threadIdx, blockIdx;
static uir_dim blockDim;
static pthread_mutex_t uir_m = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t uir_c = PTHREAD_COND_INITIALIZER;
static int uir_waiting, uir_gen;
static void __syncthreads() {
  pthread_mutex_lock(&uir_m);
  int g = uir_gen;
  if (++uir_waiting == blockDim.x) { uir_waiting = 0; uir_gen++; pthread_cond_broadcast(&uir_c); }
  else while (g == uir_gen) pthread_cond_wait(&uir_c, &uir_m);
  pthread_mutex_unlock(&uir_m);
}
// week 9: a warp's 32 threads wait for each other at __syncwarp(), and wmma runs a warp's tile on the CPU.
// Every lane computes the whole tile; lane 0 stores it, between two warp barriers.
static pthread_mutex_t uir_wm = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t uir_wc = PTHREAD_COND_INITIALIZER;
static int uir_wwait[32], uir_wgen[32];
static void __syncwarp(unsigned = 0xffffffffu) {
  int w = threadIdx.x / 32, n = blockDim.x - 32 * w; if (n > 32) n = 32;
  pthread_mutex_lock(&uir_wm);
  int g = uir_wgen[w];
  if (++uir_wwait[w] == n) { uir_wwait[w] = 0; uir_wgen[w]++; pthread_cond_broadcast(&uir_wc); }
  else while (g == uir_wgen[w]) pthread_cond_wait(&uir_wc, &uir_wm);
  pthread_mutex_unlock(&uir_wm);
}
namespace wmma {
struct matrix_a {}; struct matrix_b {}; struct accumulator {}; struct row_major {}; struct col_major {};
enum layout_t { mem_row_major, mem_col_major };
template <class Use, int M, int N, int K, class T, class L = void> struct fragment {
  static_assert(M == 16 && N == 16 && K == 16, "the emulator has 16x16x16 tiles only");
  enum { num_elements = 256 }; T x[256];
};
template <class Use, class T, class L> void load_matrix_sync(fragment<Use, 16, 16, 16, T, L> &f, const T *p, unsigned ld) {
  bool col = std::is_same<L, col_major>::value;
  for (int i = 0; i < 16; i++) for (int j = 0; j < 16; j++) f.x[i * 16 + j] = col ? p[j * ld + i] : p[i * ld + j];
}
template <class T> void load_matrix_sync(fragment<accumulator, 16, 16, 16, T> &f, const T *p, unsigned ld, layout_t l) {
  for (int i = 0; i < 16; i++) for (int j = 0; j < 16; j++) f.x[i * 16 + j] = l == mem_col_major ? p[j * ld + i] : p[i * ld + j];
}
template <class T> void store_matrix_sync(T *p, const fragment<accumulator, 16, 16, 16, T> &f, unsigned ld, layout_t l) {
  __syncwarp();
  if (threadIdx.x % 32 == 0) for (int i = 0; i < 16; i++) for (int j = 0; j < 16; j++) (l == mem_col_major ? p[j * ld + i] : p[i * ld + j]) = f.x[i * 16 + j];
  __syncwarp();
}
template <class F, class V> void fill_fragment(F &f, V v) { for (auto &e : f.x) e = v; }
template <class LA, class LB> void mma_sync(fragment<accumulator, 16, 16, 16, int> &d, const fragment<matrix_a, 16, 16, 16, signed char, LA> &a,
                                            const fragment<matrix_b, 16, 16, 16, signed char, LB> &b, const fragment<accumulator, 16, 16, 16, int> &c) {
  int r[256];
  for (int i = 0; i < 16; i++) for (int j = 0; j < 16; j++) {
    unsigned s = (unsigned)c.x[i * 16 + j];
    for (int k = 0; k < 16; k++) s += (unsigned)((int)a.x[i * 16 + k] * (int)b.x[k * 16 + j]);
    r[i * 16 + j] = (int)s;
  }
  for (int e = 0; e < 256; e++) d.x[e] = r[e];
}
}
struct uir_job { int b, t; std::function<void()> *f; };
static void *uir_thread(void *p) { uir_job *j = (uir_job *)p; blockIdx.x = j->b; threadIdx.x = j->t; (*j->f)(); return 0; }
static void uir_launch(int grid, int block, std::function<void()> f) {
  blockDim.x = block;
  std::vector<pthread_t> th(block); std::vector<uir_job> jobs(block);
  for (int b = 0; b < grid; b++) {
    for (int t = 0; t < block; t++) { jobs[t] = uir_job{b, t, &f}; pthread_create(&th[t], 0, uir_thread, &jobs[t]); }
    for (int t = 0; t < block; t++) pthread_join(th[t], 0);
  }
}
#define UIR_LAUNCH(k, g, b, ...) uir_launch((g), (b), [&] { k(__VA_ARGS__); })
"""
CUDA_PRELUDE = ("#include <mma.h>\nusing namespace nvcuda;   /* week 9: wmma:: for tensor cores */\n"
                "#define UIR_LAUNCH(k, g, b, ...) do { if ((g) > 0) k<<<(g), (b)>>>(__VA_ARGS__); } while (0)\n")

def local_blobs(h, names, d):
  """Copy url= data files next to the harness and open them by name, so the build also works inside a container."""
  for b in O.all_nodes(names):
    if b.op == 'buffer' and isinstance(b.arg[3], O.Blob):
      path = b.arg[3].path; local = f"data_{b.arg[1]}.bin"
      shutil.copyfile(path, os.path.join(d, local)); h = h.replace(path.replace(chr(92), '/'), local)
  return h

def cuda_timed_harness(names):
  """Real CUDA only: copy in, one warm-up launch, then time one launch with CUDA events. Prints 'kernel SECONDS'."""
  h = cuda_harness(names, False)
  outs = O.final_versions(names)
  bufs = {u.arg[1]: u for u in O.all_nodes(names) if u.op == 'buffer'}
  call = next(l for l in h.split('\n') if l.strip().startswith('kernel('))
  dev = ''.join(f"  {CT[bufs[k].dtype]} *d{k}; cudaMalloc((void **)&d{k}, sizeof b{k}); cudaMemcpy(d{k}, b{k}, sizeof b{k}, cudaMemcpyHostToDevice);\n" for k in outs)
  args = ', '.join(f"d{k}" for k in outs)
  timed = (f"  kernel({args}); cudaDeviceSynchronize();   /* warm up */\n"
           "  cudaEvent_t e0, e1; cudaEventCreate(&e0); cudaEventCreate(&e1); cudaEventRecord(e0);\n"
           f"  kernel({args}); cudaEventRecord(e1); cudaEventSynchronize(e1);\n"
           '  float ms_; cudaEventElapsedTime(&ms_, e0, e1); fprintf(stderr, "kernel %.9f\\n", ms_ / 1000.0);\n')
  return '#include <cuda_runtime.h>\n' + h.replace(call + '\n', dev + timed)

def cuda_speed(out, names, speed, week=None):
  """# cuda speed: X. Real CUDA only: your kernel against the reference's, best of 3, interleaved."""
  ref = O.render_c(names, 'cuda', week)
  with tempfile.TemporaryDirectory() as d:
    for tag, src in (('mine', out), ('ref', ref)):
      open(os.path.join(d, f'{tag}.cu'), 'w', encoding='utf-8').write(src)
    open(os.path.join(d, 'main.cu'), 'w', encoding='utf-8').write(local_blobs(cuda_timed_harness(names), names, d))
    open(os.path.join(d, 'prelude.h'), 'w', encoding='utf-8').write(CUDA_PRELUDE)
    nv = "nvcc -O2 -arch=native -fmad=false -prec-div=true -diag-suppress 177 -include prelude.h"
    script = (f"{nv} mine.cu main.cu -o mine && {nv} ref.cu main.cu -o ref && "
              "for i in 1 2 3; do ./mine 2>&1 >/dev/null | sed 's/^/mine /'; ./ref 2>&1 >/dev/null | sed 's/^/ref /'; done")
    cmd = (['docker', 'run', '--rm', '--gpus', 'all', '-v', f"{d}:/w", '-w', '/w', '--entrypoint', 'sh', CUDA_DOCKER, '-c', script]
           if CUDA_DOCKER and not NVCC else ['sh', '-c', script])
    r = subprocess.run(cmd, capture_output=True, timeout=600, cwd=d)
    if r.returncode != 0: return "timing build failed:\n" + indent((r.stderr or r.stdout).decode('utf-8', 'replace'))
    best = {}
    for tag, t in re.findall(r"^(mine|ref) kernel ([0-9.e-]+)", r.stdout.decode(), re.M): best[tag] = min(best.get(tag, 1e9), float(t))
    if set(best) != {'mine', 'ref'}: return "couldn't read the kernel times"
    if best['mine'] > best['ref'] / speed:
      return f"too slow on the GPU: {best['mine'] * 1e3:.2f} ms, the target is at most {best['ref'] / speed * 1e3:.2f} ms (the reference took {best['ref'] * 1e3:.2f} ms)"
  return None

def cuda_harness(names, real, timed=False):
  """main(): fill the buffers, call your host kernel() with pointers it can use, print every buffer."""
  outs = O.final_versions(names)
  bufs = {u.arg[1]: u for u in O.all_nodes(names) if u.op == 'buffer'}
  h = harness(names, timed=timed)
  sig = 'void kernel(' + (', '.join(f"{CT[bufs[k].dtype]} *b{k}" for k in outs) or 'void') + ');'
  h = h.replace(next(l for l in h.split('\n') if l.startswith('void kernel(')), sig)
  if not real: return h
  # real CUDA: copy each buffer to the device and back around the call
  call = next(l for l in h.split('\n') if l.strip().startswith('kernel('))
  dev = ''.join(f"  {CT[bufs[k].dtype]} *d{k}; cudaMalloc((void **)&d{k}, sizeof b{k}); cudaMemcpy(d{k}, b{k}, sizeof b{k}, cudaMemcpyHostToDevice);\n" for k in outs)
  back = ''.join(f"  cudaMemcpy(b{k}, d{k}, sizeof b{k}, cudaMemcpyDeviceToHost);\n" for k in outs)
  dcall = '  kernel(' + ', '.join(f"d{k}" for k in outs) + '); cudaDeviceSynchronize();\n'
  return '#include <cuda_runtime.h>\n' + h.replace(call + '\n', dev + dcall + back)

def reference_buffers(names):
  """The reference compiler's C kernel, built and run: {slot: (dtype, values)} for every printed buffer."""
  outs = O.final_versions(names)
  with tempfile.TemporaryDirectory() as d:
    exe = build_timed(d, 'ref', O.render_c(names), names)
    if not os.path.exists(exe): return "grader error: the reference kernel " + exe
    r = subprocess.run([exe], capture_output=True, timeout=300)
  got = {}
  for line in r.stdout.decode().split('\n'):
    if line.strip(): slot, v = line.split(); got.setdefault(int(slot), []).append(v)
  return {k: (outs[k].dtype, tuple(struct.unpack('<f', struct.pack('<I', int(v, 16)))[0] if outs[k].dtype == 'f32' else int(v) for v in vs)) for k, vs in got.items()}

def grade_cuda(cmd, text, base=None, h=None):
  rc, out, err = call(cmd, 'render-cuda', text, base)
  if h and h.get('cuda_invalid'):                 # not in kernel form: run and render take it, render-cuda must refuse
    return None if rc == 2 else f"render-cuda should exit 2 (the program isn't in kernel form), but exited {rc}"
  if rc != 0: return f"render-cuda exited {rc}\n    stderr: {err.strip()[:300]}"
  names = O.parse(text, base)[0]
  real = bool(NVCC or CUDA_DOCKER)
  if h and h.get('cuda_speed') and not real:     # no GPU: just make sure it builds (the small cuda tests check the bits)
    if not CXX: return "no C++ compiler (clang++ or g++) for the CUDA emulator, and no nvcc"
    with tempfile.TemporaryDirectory() as d:
      open(os.path.join(d, 'kernel.cu'), 'w', encoding='utf-8').write(out); open(os.path.join(d, 'prelude.h'), 'w', encoding='utf-8').write(EMULATOR)
      c = subprocess.run([CXX, '-std=c++14', '-fsyntax-only', '-x', 'c++', '-include', os.path.join(d, 'prelude.h'), os.path.join(d, 'kernel.cu')], capture_output=True, timeout=120)
      return None if c.returncode == 0 else "your CUDA doesn't compile (as C++, in the emulator):\n" + indent(c.stderr.decode('utf-8', 'replace').replace(d + os.sep, ''))
  if h and h.get('cuda_speed'): want = reference_buffers(names)        # too big to interpret: the reference's C gives the bits
  else:
    outs_ = O.final_versions(names)
    skip = {k for k, v in outs_.items() if v.op == 'buffer' and isinstance(v.arg[3], O.Blob)}   # unchanged input files aren't printed
    want = {k: v for k, v in O.final_buffers(names).items() if k not in skip}
  if isinstance(want, str): return want
  real = bool(NVCC or CUDA_DOCKER)
  if not real and not CXX: return "no C++ compiler (clang++ or g++) for the CUDA emulator, and no nvcc"
  with tempfile.TemporaryDirectory() as d:
    open(os.path.join(d, 'kernel.cu'), 'w', encoding='utf-8').write(out)
    open(os.path.join(d, 'main.cu'), 'w', encoding='utf-8').write(local_blobs(cuda_harness(names, real), names, d))
    open(os.path.join(d, 'prelude.h'), 'w', encoding='utf-8').write(CUDA_PRELUDE if real else EMULATOR)
    if real:
      build = "nvcc -O2 -arch=native -fmad=false -prec-div=true -diag-suppress 177 -include prelude.h kernel.cu main.cu -o a.out"
      run_cmd = (['docker', 'run', '--rm', '--gpus', 'all', '-v', f"{d}:/w", '-w', '/w', '--entrypoint', 'sh', CUDA_DOCKER, '-c', build + ' && ./a.out']
                 if CUDA_DOCKER and not NVCC else ['sh', '-c', build + ' && ./a.out'])
      try: r = subprocess.run(run_cmd, capture_output=True, timeout=300, cwd=d)
      except subprocess.TimeoutExpired: return "CUDA build and run took over 300 s"
      if r.returncode != 0: return "your CUDA failed to build or run:\n" + indent((r.stderr or r.stdout).decode('utf-8', 'replace'))
    else:
      exe = os.path.join(d, 'a.exe' if os.name == 'nt' else 'a.out')
      c = subprocess.run([CXX, '-std=c++14', '-O1', '-x', 'c++', '-include', os.path.join(d, 'prelude.h'), os.path.join(d, 'kernel.cu'), os.path.join(d, 'main.cu'), '-o', exe, '-lpthread'],
                         capture_output=True, timeout=120)
      if c.returncode != 0: return "your CUDA doesn't compile (as C++, in the emulator):\n" + indent(c.stderr.decode('utf-8', 'replace').replace(d + os.sep, ''))
      try: r = subprocess.run([exe], capture_output=True, timeout=TIMEOUT * 3)
      except subprocess.TimeoutExpired: return "the emulated kernel didn't finish: a thread waiting at a __syncthreads() the others never reach?"
      if r.returncode != 0: return f"the emulated kernel crashed (exit {r.returncode})"
    got = {}
    for line in r.stdout.decode().split('\n'):
      if re.fullmatch(r"[0-9]+ -?[0-9a-f]+", line.strip()): slot, v = line.split(); got.setdefault(int(slot), []).append(v)
  for slot, (dt, data) in want.items():
    g = got.get(slot, [])
    if len(g) != len(data): return f"buffer {slot}: read {len(g)} values, expected {len(data)}"
    for i, (x, y) in enumerate(zip(data, g)):
      if dt == 'f32':
        gb = struct.pack('<I', int(y, 16)); ok = (math.isnan(x) and math.isnan(struct.unpack('<f', gb)[0])) or O.fbits(x) == gb
      else: ok = int(y) == int(x)
      if not ok: return f"buffer {slot}[{i}]: expected {x!r}, your kernel left {y}" + ("" if real else " (in the emulator)")
  if h and h.get('cuda_speed') and real: return cuda_speed(out, names, h['cuda_speed'], next((int(m) for m in re.findall(r'week(\d+)', base or '')), None))   # without a GPU: bits only
  return None

def show(args): return ', '.join(f"param {i} = {a.arg if a.op == 'const' else [s.arg for s in a.src]!r}" for i, a in enumerate(args))
def indent(s): return '\n'.join('      ' + l for l in s.strip().splitlines()[:40])
def rel(f): return os.path.relpath(f, ROOT).replace('\\', '/')

def files(week, k):
  fs = sorted(glob.glob(os.path.join(ROOT, 'tests', f'week{week}', '**', '*.uir'), recursive=True))
  return [f for f in fs if not k or k.replace('\\', '/') in rel(f)]

def grade(cmd, f):
  try:
    text = O.read_text(f); h = headers(text); base = os.path.dirname(f)
    if h.get('cuda'): return grade_cuda(cmd, text, base, h)
    if h.get('render'): return grade_render(cmd, text, base, h)
    return grade_simplify(cmd, text, h['max_ops']) if 'max_ops' in h else grade_run(cmd, text, base)
  except Exception as e:                            # one broken case fails that case, never the whole run
    return f"grader error on this test: {type(e).__name__}: {e}"

def run_suite(cmd, fs, verbose, jobs):
  with ThreadPoolExecutor(max_workers=jobs) as ex: results = list(ex.map(lambda f: grade(cmd, f), fs))
  bad = [(f, r) for f, r in zip(fs, results) if r]
  for f, r in bad: print(f"FAIL {rel(f)}\n    {r if verbose else r.splitlines()[0]}")
  print(f"\n{len(fs) - len(bad)} / {len(fs)} passed" + ("" if verbose or not bad else "   (-v for details)"))
  return bad

def check_tests(fs):
  # every header must agree with the oracle, and every simplify target must be reachable by the oracle's own simplify
  bad = 0
  for f in fs:
    try:
      text = O.read_text(f); h = headers(text)
      if h.get('cuda'): r = grade_cuda(ORACLE, text, os.path.dirname(f), h)
      elif h.get('render'): r = grade_render(ORACLE, text, os.path.dirname(f), h)
      elif 'max_ops' in h:
        try: O.parse(text)[0]['out']; r = grade_simplify(ORACLE, text, h['max_ops'])
        except (O.UIRError, KeyError) as e: r = f"simplify test must parse and define %out: {e}"
      elif 'expect' not in h: r = "missing '# expect: pass|assert_fail|invalid' header"
      else:
        got, msg = oracle_run(text, os.path.dirname(f))
        r = None if got == h['expect'].split()[0] else f"header says {h['expect']}, oracle says {got}" + (f" ({msg})" if msg else "")
    except Exception as e: r = f"couldn't check: {type(e).__name__}: {e}"
    if r: bad += 1; print(f"BAD  {os.path.relpath(f)}\n    {r}")
  print(f"\n{len(fs) - bad} / {len(fs)} tests agree with the oracle")
  return bad

def main():
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument('--compiler'); ap.add_argument('--week', type=int, default=1)
  ap.add_argument('-k', default=''); ap.add_argument('-v', action='store_true')
  ap.add_argument('--skip', default='', help='leave out tests whose path contains this (e.g. mnist)')
  ap.add_argument('--cuda-docker', default='', help='run CUDA tests in this Docker image with --gpus all (e.g. nvidia/cuda:12.6.3-devel-ubuntu22.04)')
  ap.add_argument('--jobs', type=int, default=os.cpu_count() or 4, help='parallel tests (use 1 if your compiler shares a lock, e.g. dune exec)')
  ap.add_argument('--check-tests'); ap.add_argument('--self-check', action='store_true')
  a = ap.parse_args()
  sys.setrecursionlimit(100000); threading.stack_size(64 * 1024 * 1024)   # oracle evaluation of nested calls recurses
  global CUDA_DOCKER
  if a.cuda_docker: CUDA_DOCKER = a.cuda_docker
  if a.check_tests:
    fs = sorted(glob.glob(os.path.join(a.check_tests, '**', '*.uir'), recursive=True))
    if not fs: sys.exit(f"no .uir files in {a.check_tests}")
    sys.exit(1 if check_tests(fs) else 0)
  fs = [f for f in files(a.week, a.k) if not a.skip or a.skip not in rel(f)]
  if not fs: sys.exit(f"no tests for week {a.week}" + (f" matching '{a.k}'" if a.k else ""))
  if a.self_check: sys.exit(1 if check_tests(fs) else 0)
  if not a.compiler: ap.error("--compiler is required")
  # on Windows shlex keeps quotes in non-posix mode; strip them so "C:/Program Files/x.exe" works
  cmd = [a.compiler] if os.path.exists(a.compiler) else [t.strip('"') for t in shlex.split(a.compiler, posix=os.name != 'nt')]
  sys.exit(1 if run_suite(cmd, fs, a.v, max(1, a.jobs)) else 0)

if __name__ == '__main__': main()
