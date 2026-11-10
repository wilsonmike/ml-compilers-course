#!/usr/bin/env python3
"""Everything that must hold before a push, in one command. Runs the checks in parallel.

  python tools/check.py            # about a minute: lint, site, spec, every week's tests, every exercise
  python tools/check.py --full     # also the MNIST training test (30 s) and the planted-bug run (5 min)

Exit 0 means all of it passed. OCaml exercises are checked when `ocaml` is on PATH, or with
--ocaml "docker run --rm -i ocaml/opam:alpine-ocaml-5.2 ocaml".
"""
import os, sys, time, shutil, hashlib, argparse, subprocess
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

def digest(folder):
  h = hashlib.sha256()
  for d, _, fs in sorted(os.walk(folder)):
    for f in sorted(fs): h.update(f.encode()); h.update(open(os.path.join(d, f), 'rb').read())
  return h.hexdigest()

def main():
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument('--full', action='store_true'); ap.add_argument('--ocaml')
  a = ap.parse_args()
  weeks = sorted(int(d[4:]) for d in os.listdir(os.path.join(ROOT, 'tests')) if d.startswith('week'))
  checks = [('design and copy lint', [PY, 'tools/design_lint.py']),
            ('site: html, quizzes, links, scripts', [PY, 'tools/check_site.py']),
            ('week 6 spec matches the oracle', [PY, 'tools/check_spec_w6.py'])]
  for w in weeks:
    checks.append((f'week {w} tests agree with the oracle', [PY, 'tools/test.py', '--self-check', '--week', str(w), '--jobs', '2'] + ([] if a.full else ['--skip', 'mnist'])))
  ocaml = a.ocaml or (shutil.which('ocaml') and 'ocaml')
  checks.append(('exercises: solutions pass, starters fail', [PY, '_reference/check_exercises.py'] + (['--ocaml', ocaml] if ocaml else ['--skip-lang', 'ocaml'])))
  if a.full: checks.append(('planted bugs are all caught', [PY, '_reference/mutants.py']))

  data = os.path.join(ROOT, 'site', 'data', 'ex'); before = digest(data)
  t0 = time.time()
  def run(c):
    s = time.time(); p = subprocess.run(c[1], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return c[0], p.returncode, (p.stdout + p.stderr).strip(), time.time() - s
  with ThreadPoolExecutor(max_workers=6) as ex: results = list(ex.map(run, checks))
  subprocess.run([PY, 'tools/build_static.py'], cwd=ROOT, capture_output=True)
  results.append(('site/data/ex is up to date', 0 if digest(data) == before else 1,
                  'it was stale: tools/build_static.py has now rebuilt it, so commit the change', 0))
  bad = 0
  for name, rc, out, dt in results:
    print(f"{'ok  ' if rc == 0 else 'FAIL'}  {name}" + (f"  ({dt:.0f} s)" if dt >= 1 else ''))
    if rc:
      bad += 1
      print('\n'.join('      ' + l for l in out.splitlines()[-15:]))
  if not ocaml: print('      (OCaml exercises skipped: no ocaml on PATH. Pass --ocaml "docker run --rm -i ocaml/opam:alpine-ocaml-5.2 ocaml".)')
  print(f"\n{len(results) - bad} / {len(results)} checks passed in {time.time() - t0:.0f} s")
  sys.exit(1 if bad else 0)

if __name__ == '__main__': main()
