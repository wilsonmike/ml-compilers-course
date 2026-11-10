#!/usr/bin/env python3
"""Time your rendered kernel and count the useful work it does.

  python tools/bench.py --compiler PATH/TO/your.exe FILE.uir [--runs 3]

Renders FILE with your compiler, builds it with the grader's harness at -O2 (without the sanitizers,
which slow code down), runs it and prints the best time over the runs, the FLOPs and FLOP/s.
FLOPs: one per element of each elementwise op (a math op counts as one), size minus result size per
reduce, times the trip count of any hand-written loops around it. Movement ops and loads count zero.
"""
import os, re, sys, time, shlex, argparse, tempfile, subprocess, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location('grader', os.path.join(ROOT, 'tools', 'test.py'))
T = importlib.util.module_from_spec(_s); _s.loader.exec_module(T)
O = T.O
FREE = {'cast', 'bitcast', 'detach'}

def flops(names):
  outs = O.final_versions(names)
  top = [u for u in O.all_nodes(names) if not O.opens(u) and u.op != 'range']
  total = 0
  for u in O.all_nodes(names):
    trips = 1
    for r in O.opens(u): trips *= max(r.src[0].arg, 0) if r.src[0].op == 'const' else 1
    if u.op in O.ALU and u.op not in FREE: total += O.prod(u.shape) * trips
    elif u.op == 'reduce': total += (O.prod(u.src[0].shape) - O.prod(u.shape)) * trips
  return total

def main():
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument('--compiler', required=True); ap.add_argument('file'); ap.add_argument('--runs', type=int, default=3)
  a = ap.parse_args()
  if not T.CC: sys.exit("no C compiler found (clang or gcc)")
  cmd = [a.compiler] if os.path.exists(a.compiler) else [t.strip('"') for t in shlex.split(a.compiler, posix=os.name != 'nt')]
  text, base = O.read_text(a.file), os.path.dirname(os.path.abspath(a.file))
  names = O.parse(text, base)[0]
  t0 = time.perf_counter(); rc, out, err = T.call(cmd, 'render', text, base, 600); t_render = time.perf_counter() - t0
  if rc != 0: sys.exit(f"render exited {rc}: {err.strip()[:300]}")
  with tempfile.TemporaryDirectory() as d:          # the grader's timed build: -O2, no sanitizers, threads linked
    t0 = time.perf_counter(); exe = T.build_timed(d, 'k', out, names); t_cc = time.perf_counter() - t0
    if not os.path.exists(exe): sys.exit("your C " + exe)
    best = None
    for _ in range(max(1, a.runs)):
      r = subprocess.run([exe], capture_output=True)
      if r.returncode != 0: sys.exit(f"the kernel exited {r.returncode}")
      m = re.search(r"kernel ([0-9.e-]+)", r.stderr.decode())
      best = float(m.group(1)) if best is None else min(best, float(m.group(1)))
  n = flops(names)
  print(f"render   {t_render:8.3f} s   ({len(out.encode())} bytes of C)")
  print(f"cc -O2   {t_cc:8.3f} s")
  print(f"kernel   {best:8.4f} s   best of {max(1, a.runs)}, {T.THREADS} hardware threads")
  print(f"work     {n / 1e9:8.3f} GFLOP")
  if best > 0: print(f"speed    {n / best / 1e9:8.3f} GFLOP/s")

if __name__ == '__main__': main()
