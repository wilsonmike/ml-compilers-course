#!/usr/bin/env python3
"""The course server: serves the lessons and runs your exercise code locally.

  python tools/serve.py                 # http://127.0.0.1:4111
  python tools/serve.py --port 5000
  python tools/serve.py --ocaml "docker run --rm -i ocaml/opam:alpine-ocaml-5.2 ocaml"   # no local OCaml

It compiles and runs code you type into the lesson editors, so it only listens on 127.0.0.1 and only
accepts requests from its own pages (Host check + a custom header that cross-site pages can't send).
"""
import os, sys, re, json, glob, shlex, shutil, secrets, argparse, tempfile, subprocess, importlib.util
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXDIR = os.path.join(ROOT, 'exercises')
_spec = importlib.util.spec_from_file_location('oracle', os.path.join(ROOT, '_reference', 'uirc.py'))
O = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(O)
CAP = 4000                      # max chars of compiler/program output sent back

def load(ex_id):
  if not re.fullmatch(r"[\w-]+", ex_id or ''): return None
  p = os.path.join(EXDIR, ex_id + '.json')
  return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None

def public(ex):
  # what the page may see: no hidden tests
  samples = [{k: t[k] for k in ('expr', 'args', 'expect') if k in t} | {'label': label(ex, t)} for t in ex['tests'] if t.get('sample')]
  return {'id': ex['id'], 'lang': ex['lang'], 'title': ex.get('title', ''), 'starter': ex['starter'],
          'samples': samples, 'ntests': len(ex['tests']), 'max_ops': ex.get('max_ops'), 'hints': ex.get('hints', []),
          **({'prompt': ex['prompt']} if ex.get('prompt') else {})}

def label(ex, t):
  if 'data' in t: return '\n'.join(f"buffer slot {k} starts as [{' '.join(map(str, v))}]" for k, v in t['data'].items()) + f"\nfinal contents of slot {t.get('out', ex.get('out_slot', 0))}"
  if 'args' in t: return f"%out({', '.join(map(str, t['args']))})"
  return t.get('expr', '')

EXT = {'ocaml': 'ml', 'c': 'c', 'uir': 'uir', 'python': 'py'}
def solution(ex):
  # the "show answer" button: the reference solution plus a short why. Only ever sent when the student asks.
  p = os.path.join(ROOT, '_reference', 'solutions', f"{ex['id']}.{EXT[ex['lang']]}")
  return {'code': open(p, encoding='utf-8').read() if os.path.exists(p) else None, 'explain': ex.get('explain', '')}

def clip(s): return s if len(s) <= CAP else s[:CAP] + f"\n... ({len(s) - CAP} more chars)"

def run_proc(cmd, stdin=None, timeout=10):
  try:
    p = subprocess.run(cmd, input=stdin, capture_output=True, text=True, timeout=timeout, encoding='utf-8', errors='replace')
    return p.returncode, p.stdout, p.stderr
  except subprocess.TimeoutExpired: return 'timeout', '', f'timed out after {timeout}s (infinite loop?)'
  except OSError as e: return 'missing', '', str(e)

def split_marked(out, nonce):
  # harness prints "\n<nonce><i> <value>" per test; anything else is the user's own output
  got, user = {}, []
  for line in out.splitlines():
    m = re.match(re.escape(nonce) + r"(\d+) ?(.*)$", line)
    if m: got[int(m.group(1))] = m.group(2)
    elif line.strip(): user.append(line)
  return got, '\n'.join(user)

# ---------------- language runners: each returns (compile_error or None, [got per test], stdout) ----------------

def run_ocaml(ex, code, tests, cfg):
  nonce = '@@' + secrets.token_hex(4) + ':'
  lines = [code.rstrip(), ';;', f"let __show = {ex['show']};;"]
  for i, t in enumerate(tests):
    lines.append(f'let () = print_string "\\n{nonce}{i} "; (match __show ({t["expr"]}) with s -> print_string s '
                 f'| exception e -> print_string ("exception " ^ Printexc.to_string e)); print_newline ();;')
  rc, out, err = run_proc(cfg.ocaml + ['-stdin'], '\n'.join(lines) + '\n', timeout=cfg.timeout)
  if rc == 'missing': return "OCaml isn't installed (or isn't on PATH). See week 0, lesson 0.6, or start the server with --ocaml.", [], ''
  if rc == 'timeout': return err, [], ''
  got, user = split_marked(out, nonce)
  if not got and rc != 0:
    n = code.count('\n') + 1
    if re.search(r'line (\d+)', err) and int(re.search(r'line (\d+)', err).group(1)) > n:
      err += "\n(The error is in the test harness: keep the function name and type the starter code gives you.)"
    return clip(err.replace('File "(stdin)", ', '')), [], clip(user)
  return None, [got.get(i, f"crashed: {err.strip()[:200]}") for i in range(len(tests))], clip(user)

def UB_TRAP(cc):
  # the render grader's flags: undefined behavior (signed overflow, INT_MIN / -1, bad shifts) traps instead of passing by luck
  return ['-fsanitize=undefined', '-fsanitize-trap=undefined'] if 'clang' in os.path.basename(cc) else ['-fsanitize=undefined', '-fsanitize-undefined-trap-on-error']

def run_c(ex, code, tests, cfg):
  if not cfg.cc: return "No C compiler found (looked for clang, gcc, cc).", [], ''
  nonce = '@@' + secrets.token_hex(4) + ':'
  cases = '\n'.join(f'    case {i}: printf("\\n{nonce}{i} {ex["show"]}\\n", ({t["expr"]})); break;' for i, t in enumerate(tests))
  src = ("#include <stdio.h>\n#include <stdlib.h>\n#include <stdint.h>\n#include <string.h>\n#include <math.h>\n#line 1 \"solution.c\"\n"
         + code.rstrip() + "\n#line 1 \"tests.c\"\nint main(int argc, char **argv) {\n  setvbuf(stdout, NULL, _IONBF, 0);\n  switch (atoi(argv[1])) {\n"
         + cases + "\n  }\n  return 0;\n}\n")
  with tempfile.TemporaryDirectory() as d:
    c, exe = os.path.join(d, 'solution.c'), os.path.join(d, 'a.exe' if os.name == 'nt' else 'a.out')
    open(c, 'w', encoding='utf-8').write(src)
    rc, out, err = run_proc([cfg.cc, '-O1', '-w', '-std=gnu11', *UB_TRAP(cfg.cc), c, '-o', exe, '-lm'], timeout=30)
    if rc != 0:
      if 'tests.c' in err: err += "\n(The error is in the test harness: keep the function name and signature the starter code gives you.)"
      return clip(err.replace(d + os.sep, '').replace(d + '/', '')), [], ''
    res, users = [], []
    for i in range(len(tests)):
      rc, out, err = run_proc([exe, str(i)], timeout=cfg.timeout)
      got, user = split_marked(out, nonce)
      if user: users.append(user)
      res.append(got[i] if i in got else ('timed out: an infinite loop, or undefined behavior such as INT_MIN / -1, which hangs on Windows' if rc == 'timeout' else f"crashed (exit code {rc})" + (f": {err.strip()[:200]}" if err.strip() else '')))
    return None, res, clip('\n'.join(users))

def fmt(v, dt):
  if isinstance(v, tuple): return '[' + ' '.join(fmt(x, dt) for x in v) + ']'
  return O.lit(O.const(v, dt))

def with_data(code, data):
  # replace each slot's initial contents: rewrite (or add) data=[...] on that buffer's line
  out = []
  for line in code.split('\n'):
    m = re.search(r"\bbuffer\b.*\bslot=([0-9]+)", line.split('#', 1)[0])
    if m and m.group(1) in data:
      body = re.sub(r"[ \t]+data=\[[^\]]*\]", "", line.split('#', 1)[0]).rstrip()
      line = body + f" data=[{' '.join(str(v).lower() if isinstance(v, bool) else str(v) for v in data[m.group(1)])}]"
    out.append(line)
  return '\n'.join(out)

def run_uir_buffers(ex, code, tests):
  # week 2 programs: each test sets buffer contents and checks one buffer's final contents
  try: O.parse(code)
  except O.UIRError as e: return f"invalid .uir: {e}", [], ''
  # week 7: axes never change results, so an exercise about them also names what the program must contain
  stripped = '\n'.join(l.split('#', 1)[0] for l in code.split('\n'))           # comments don't count
  for pat, why in ex.get('require', []):
    if not re.search(pat, stripped): return why, [], ''
  res = []
  for t in tests:
    try:
      fb = O.final_buffers(O.parse(with_data(code, {str(k): v for k, v in t.get('data', {}).items()}))[0])
      slot = t.get('out', ex.get('out_slot', 0))
      if slot not in fb: res.append(f"error: no buffer with slot {slot}"); continue
      dt, vals = fb[slot]
      res.append(fmt(tuple(vals), dt))
    except O.UIRError as e: res.append(f"error: {e}")
  return None, res, ''

def run_uir(ex, code, tests, cfg):
  if ex.get('mode') == 'buffers': return run_uir_buffers(ex, code, tests)
  # the program must define %out over params; each test calls it with args
  try:
    names = O.parse(code)[0]
    if 'out' not in names: return "your program must define %out", [], ''
    out = names['out']
    if ex.get('max_ops') is not None and (n := O.count_ops(out)) > ex['max_ops']:
      return f"%out uses {n} ops; this exercise allows at most {ex['max_ops']}", [], ''
  except O.UIRError as e: return f"invalid .uir: {e}", [], ''
  res = []
  for t in tests:
    try:
      args = [O.literal(str(a).lower() if isinstance(a, bool) else str(a)) for a in t['args']]
      res.append(fmt(O.evaluate(O.build('call', [out] + args, {}), None), out.dtype))
    except O.UIRError as e: res.append(f"error: {e}")
  return None, res, ''

def run_python(ex, code, tests, cfg):
  # The student's module, then a harness that evaluates each test expression in the module's namespace and prints
  # show(value). It runs isolated (-I) under this same Python, so the course needs nothing extra.
  nonce = '@@' + secrets.token_hex(4) + ':'
  harness = ("\n\n# ---- tests ----\n"
             f"__show = {ex.get('show', 'str')}\n"
             f"for __i, __e in enumerate({[t['expr'] for t in tests]!r}):\n"
             "    try:\n        __v = __show(eval(__e))\n"
             "    except Exception as __x:\n        __v = 'exception ' + type(__x).__name__ + (': ' + str(__x) if str(__x) else '')\n"
             f"    print('\\n{nonce}' + str(__i) + ' ' + str(__v), flush=True)\n")
  with tempfile.TemporaryDirectory() as d:
    path = os.path.join(d, 'solution.py')
    open(path, 'w', encoding='utf-8').write(code.rstrip() + harness)
    rc, out, err = run_proc([sys.executable, '-I', '-X', 'utf8', path], timeout=cfg.timeout)
  if rc == 'timeout': return err, [], ''
  got, user = split_marked(out, nonce)
  if not got and rc != 0:
    err = err.replace(path, 'solution.py')
    if '---- tests ----' in err or 'line ' + str(code.count('\n') + 3) in err:
      err += "\n(The error is in the test harness: keep the function name and signature the starter code gives you.)"
    return clip(err), [], clip(user)
  return None, [got.get(i, f"crashed: {err.strip()[-300:]}") for i in range(len(tests))], clip(user)

RUNNERS = {'ocaml': run_ocaml, 'c': run_c, 'uir': run_uir, 'python': run_python}

def grade(ex, code, everything, cfg):
  tests = ex['tests'] if everything else [t for t in ex['tests'] if t.get('sample')]
  err, got, user = RUNNERS[ex['lang']](ex, code, tests, cfg)
  if err: return {'ok': False, 'error': err, 'stdout': user}
  results = []
  for t, g in zip(tests, got):
    shown = t.get('sample') or not everything
    results.append({'input': label(ex, t), 'expect': t['expect'], 'got': g,
                    'pass': g.strip() == str(t['expect']).strip(), 'hidden': not shown})
  first_bad = next((r for r in results if not r['pass'] and r['hidden']), None)
  for r in results:            # reveal hidden tests that pass (as names only) and the first failing one, like LeetCode
    if r['hidden'] and r is not first_bad: r.update(input=None, expect=None, got=None)
  return {'ok': True, 'results': results, 'passed': sum(r['pass'] for r in results), 'total': len(results), 'stdout': user}

# ---------------- http ----------------

class H(SimpleHTTPRequestHandler):
  def __init__(self, *a, **k): super().__init__(*a, directory=ROOT, **k)
  def log_message(self, fmt, *args):
    line = str(args[0]) if args else ''
    if '/api/' in line or fmt.startswith('code'): sys.stderr.write(f"  {fmt % args}\n")
  def end_headers(self):
    self.send_header('Cache-Control', 'no-store'); super().end_headers()
  def host_ok(self): return self.headers.get('Host', '') in (f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}")
  def send_json(self, code, obj):
    b = json.dumps(obj).encode(); self.send_response(code)
    self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
  def do_GET(self):
    if not self.host_ok(): return self.send_error(403, 'bad host')
    path = self.path.split('?')[0]
    if path in ('/', '/index.html'): self.send_response(302); self.send_header('Location', '/site/index.html'); self.end_headers(); return
    if path.startswith(('/exercises', '/_reference', '/.git')): return self.send_error(403, 'not served')
    if path == '/api/health':
      return self.send_json(200, {'ok': True, 'ocaml': bool(self.server.cfg.ocaml_ok), 'cc': self.server.cfg.cc and os.path.basename(self.server.cfg.cc), 'uir': True, 'python': True})
    if path.startswith('/api/exercise/'):
      ex = load(path.rsplit('/', 1)[1])
      return self.send_json(200, public(ex)) if ex else self.send_json(404, {'error': 'no such exercise'})
    if path.startswith('/api/solution/'):
      ex = load(path.rsplit('/', 1)[1])
      return self.send_json(200, solution(ex)) if ex else self.send_json(404, {'error': 'no such exercise'})
    return super().do_GET()
  def do_POST(self):
    # cross-site pages can't set X-Course-Runner without a CORS preflight, which we never approve
    if not self.host_ok() or self.headers.get('X-Course-Runner') != '1' or self.path != '/api/run':
      return self.send_error(403, 'forbidden')
    try:
      body = json.loads(self.rfile.read(min(int(self.headers.get('Content-Length', 0)), 200_000)))
      ex = load(body.get('id'))
      if not ex: return self.send_json(404, {'error': 'no such exercise'})
      self.send_json(200, grade(ex, str(body.get('code', '')), bool(body.get('submit')), self.server.cfg))
    except Exception as e: self.send_json(500, {'ok': False, 'error': f"runner bug: {type(e).__name__}: {e}"})
  def do_OPTIONS(self): self.send_error(405)

def config(a):
  cfg = argparse.Namespace(timeout=a.timeout)
  cfg.ocaml = shlex.split(a.ocaml, posix=os.name != 'nt') if a.ocaml else ['ocaml']
  cfg.ocaml = [t.strip('"') for t in cfg.ocaml]
  cfg.ocaml_ok = bool(a.ocaml) or bool(shutil.which('ocaml'))
  cfg.cc = next((shutil.which(c) for c in ('clang', 'gcc', 'cc') if shutil.which(c)), None)
  return cfg

def main():
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument('--port', type=int, default=4111); ap.add_argument('--ocaml'); ap.add_argument('--timeout', type=int, default=10)
  a = ap.parse_args()
  srv = ThreadingHTTPServer(('127.0.0.1', a.port), H); srv.cfg = config(a)
  print(f"course: http://127.0.0.1:{a.port}/\n  ocaml: {'yes' if srv.cfg.ocaml_ok else 'not found (OCaml exercises will say so)'}\n  c:     {srv.cfg.cc or 'not found'}")
  try: srv.serve_forever()
  except KeyboardInterrupt: pass

if __name__ == '__main__': main()
