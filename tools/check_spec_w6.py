#!/usr/bin/env python3
# Checks that every exact definition in spec/uir-week6.md is the graph the oracle uses: the spec's
# .uir text, parsed and hash consed, must give the very same node. Run after editing either one.
import os, re, sys, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = importlib.util.spec_from_file_location('oracle', os.path.join(ROOT, '_reference', 'uirc.py'))
O = importlib.util.module_from_spec(sp); sp.loader.exec_module(O)
text = open(os.path.join(ROOT, 'spec', 'uir-week6.md'), encoding='utf-8').read()
bad = 0
for name, block in re.findall(r"### (\w+)\n.*?```\n(.*?)```", text, re.S):
  root = O.parse(block)[0]['r']
  if root is not O.math_body(name): print(f"BAD  {name}: the spec's body is not the oracle's"); bad += 1
  else: print(f"ok   {name}")
floor = re.search(r"`floor`:\n\n```\n(.*?)```", text, re.S).group(1)
x = O.UOp('param', (), 0, 'f32', ())
if O.parse(floor)[0]['r'] is not O.floor_(x): print("BAD  floor"); bad += 1
else: print("ok   floor")
sys.exit(1 if bad else 0)
