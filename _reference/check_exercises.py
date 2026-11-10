# SPOILERS. Proves every lesson exercise is gradeable: its reference solution (_reference/solutions/<id>.<ext>)
# passes ALL tests, and the starter code fails at least one (so the tests actually test something).
#   python _reference/check_exercises.py [--ocaml "docker run --rm -i ocaml/opam:alpine-ocaml-5.2 ocaml"] [-k id]
import os, sys, json, glob, argparse, importlib.util
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
_s = importlib.util.spec_from_file_location('serve', os.path.join(ROOT, 'tools', 'serve.py'))
S = importlib.util.module_from_spec(_s); _s.loader.exec_module(S)
EXT = {'ocaml': 'ml', 'c': 'c', 'uir': 'uir', 'python': 'py'}

def check(ex, cfg):
  problems = []
  if not any(t.get('sample') for t in ex['tests']): problems.append("no sample tests")
  if len(ex.get('hints', [])) < 2: problems.append("needs at least 2 hints")
  if len(ex.get('explain', '')) < 40: problems.append("needs an 'explain' for the show-answer panel")
  sol = os.path.join(HERE, 'solutions', f"{ex['id']}.{EXT[ex['lang']]}")
  if not os.path.exists(sol): return [f"missing solution {os.path.relpath(sol, ROOT)}"]
  r = S.grade(ex, open(sol, encoding='utf-8').read(), True, cfg)
  if not r['ok']: problems.append(f"solution doesn't compile: {r['error'][:400]}")
  elif r['passed'] != r['total']:
    full = S.RUNNERS[ex['lang']](ex, open(sol, encoding='utf-8').read(), ex['tests'], cfg)[1]
    bad = [(t.get('expr', t.get('args')), t['expect'], g) for t, g in zip(ex['tests'], full) if g.strip() != str(t['expect']).strip()]
    problems.append(f"solution fails {len(bad)} test(s): " + '; '.join(f"{i!r} expected {e!r} got {g!r}" for i, e, g in bad[:3]))
  r = S.grade(ex, ex['starter'], True, cfg)
  if r['ok'] and r['passed'] == r['total']: problems.append("starter code already passes every test")
  return problems

if __name__ == '__main__':
  ap = argparse.ArgumentParser(); ap.add_argument('--ocaml'); ap.add_argument('-k', default=''); ap.add_argument('--timeout', type=int, default=30)
  a = ap.parse_args(); cfg = S.config(a); k = a.k
  exs = [json.load(open(p, encoding='utf-8')) for p in sorted(glob.glob(os.path.join(ROOT, 'exercises', '*.json')))]
  exs = [e for e in exs if k in e['id']]
  with ThreadPoolExecutor(max_workers=4) as pool: res = list(pool.map(lambda e: check(e, cfg), exs))
  for e, p in zip(exs, res): print(f"{'ok  ' if not p else 'BAD '} {e['id']:34} {e['lang']:5} {len(e['tests'])} tests" + ''.join(f"\n      {x}" for x in p))
  bad = sum(bool(p) for p in res); print(f"\n{len(exs) - bad} / {len(exs)} exercises verified")
  sys.exit(1 if bad else 0)
