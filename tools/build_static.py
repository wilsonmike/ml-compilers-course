#!/usr/bin/env python3
"""Write the exercise data a hosted copy of the site needs, where the local runner isn't there.

  python tools/build_static.py

For each exercise in exercises/, writes site/data/ex/<id>.json: what the runner's /api/exercise and /api/solution
would return (the prompt's examples, the hints, and the reference answer). The hidden tests stay out. A page with no
runner shows these, so a reader on the hosted site still gets the examples, hints, and answers, and runs code locally.
"""
import os, sys, glob, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from serve import public, solution, load  # the same shapes the runner sends

def main():
  out = os.path.join(ROOT, 'site', 'data', 'ex')
  os.makedirs(out, exist_ok=True)
  ids = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, 'exercises', '*.json')))
  for old in glob.glob(os.path.join(out, '*.json')):
    if os.path.basename(old)[:-5] not in ids: os.remove(old)
  for ex_id in ids:
    ex = load(ex_id)
    data = public(ex) | {'answer': solution(ex)}
    with open(os.path.join(out, ex_id + '.json'), 'w', encoding='utf-8', newline='\n') as f:
      json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
  print(f'{len(ids)} exercises written to site/data/ex/')

if __name__ == '__main__': main()
