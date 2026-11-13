#!/usr/bin/env python3
"""Build the generated study helpers: one "test guide" page per week, at site/resources/tests-weekN.html.

  python tools/build_helpers.py

For every test: what it checks (its header comment), what kind of test it is, and the plausible bugs known to
fail it. The bugs come from the planted-bug run (python _reference/mutants.py --matrix writes _reference/.mutant_results.json);
run that first for the bug column. Bug names describe mistakes, not solutions, so they're safe to show.
"""
import os, re, glob, json, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'site', 'resources')

def bugs_by_test():
  try: entries = json.load(open(os.path.join(ROOT, '_reference', '.mutant_results.json'), encoding='utf-8'))['entries']
  except (OSError, ValueError, KeyError): return {}
  out = {}
  for e in entries.values():
    if not isinstance(e, dict) or not e.get('killed'): continue
    name = re.sub(r'^w\d+ ', '', e['name'])
    for f in e.get('fails', []):
      out.setdefault(f.replace('\\', '/').split('tests/', 1)[-1], []).append(name)
  return out

def describe(path):
  lines = [l[1:].strip() for l in open(path, encoding='utf-8').read().split('\n') if l.startswith('#')]
  kind = 'run'
  for l in lines:
    if l.startswith('expect:'): kind = 'run: ' + l.split(':', 1)[1].strip()
    elif l.startswith('simplify:'): kind = 'simplify, ' + l.split(':', 1)[1].strip()
    elif l == 'render': kind = 'render'
    elif l.startswith('render check:'): kind = 'render, ' + l.split(':', 1)[1].strip()
    elif l.startswith('speed:'): kind = 'render, speed ' + l.split(':', 1)[1].strip()
    elif l == 'cuda': kind = 'cuda'
    elif l == 'cuda: invalid': kind = 'cuda: invalid'
    elif l.startswith('cuda speed:'): kind = 'cuda, speed ' + l.split(':', 1)[1].strip()
  why = next((l for l in lines if not re.match(r'(expect|simplify|render check|time|max_bytes|speed|cuda speed):|render$|cuda$|cuda: invalid$', l)), '')
  return kind, why

def page(week, rows):
  esc = html.escape
  body = '\n'.join(
    f'    <tr><td><code>{esc(name)}</code></td><td>{esc(kind)}</td><td>{esc(why)}</td>'
    f'<td>{"<br>".join(esc(b) for b in sorted(set(bugs))) or "<span class=muted>none recorded</span>"}</td></tr>'
    for name, kind, why, bugs in rows)
  return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Week {week} Test Guide</title>
<link rel="stylesheet" href="../assets/course.css">
<script src="../assets/course.js"></script>
<style>
  .guide td:first-child {{ white-space: nowrap; }}
  .guide td {{ font-size: 0.9375rem; }}
  .filter {{ width: 100%; max-width: 28rem; font: 1rem var(--sans); padding: var(--s2) var(--s3); border: 1px solid var(--line-2); border-radius: var(--r-sm); background: var(--panel); color: var(--ink); margin: 0 0 var(--s4); }}
</style>
</head>
<body data-root="../">
<main>
  <h1>Week {week} test guide</h1>
  <p class="lede">A test failed and you don't know why? Find it here: what it checks, and the plausible bugs that are known to fail it. Then read the matching part of the <a href="../../spec/uir-week{week}.md">week {week} spec</a>.</p>
  <div class="note"><span class="label">How to use this</span>
    <p>Run <code>python tools/test.py --compiler PATH --week {week} -v</code>, copy the failing test's name, and search below. "Bugs known to fail it" lists mistakes that were planted in the reference compiler and caught by this test, so one of them is a good first guess. It's not a complete list, and the <a href="debugging.html">debugging guide</a> covers what to do when none fit.</p>
  </div>
  <input class="filter" type="search" placeholder="Filter by test name, kind, or words" aria-label="Filter tests" oninput="for (const r of document.querySelectorAll('.guide tbody tr')) r.hidden = !r.textContent.toLowerCase().includes(this.value.toLowerCase())">
  <div class="tablewrap bleed">
  <table class="guide">
    <thead><tr><th>test</th><th>kind</th><th>what it checks</th><th>bugs known to fail it</th></tr></thead>
    <tbody>
{body}
    </tbody>
  </table>
  </div>
</main>
</body>
</html>
'''

def main():
  os.makedirs(OUT, exist_ok=True)
  bugs = bugs_by_test()
  for wdir in sorted(glob.glob(os.path.join(ROOT, 'tests', 'week*'))):
    week = int(re.search(r'week(\d+)$', wdir).group(1))
    rows = []
    for f in sorted(glob.glob(os.path.join(wdir, '**', '*.uir'), recursive=True)):
      rel = os.path.relpath(f, os.path.join(ROOT, 'tests')).replace('\\', '/')
      kind, why = describe(f)
      rows.append((rel.split('/', 1)[1][:-4], kind, why, bugs.get(rel, [])))
    open(os.path.join(OUT, f'tests-week{week}.html'), 'w', encoding='utf-8', newline='\n').write(page(week, rows))
    print(f"week {week}: {len(rows)} tests, {sum(1 for r in rows if r[3])} with known bugs")

if __name__ == '__main__': main()
