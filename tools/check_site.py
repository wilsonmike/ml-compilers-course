"""Checks every page of the site: HTML nesting, quizzes well formed (an answer key that is one of the options,
a hint and an explanation), exercises exist and have solutions, internal links resolve, ids unique, and every
inline <script> parses (node --check, when node is installed).

  python tools/check_site.py
"""
import os, re, sys, glob, json, html, shutil, tempfile, subprocess
from html.parser import HTMLParser
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'site')
problems = []

class P(HTMLParser):
  VOID = {'br', 'img', 'input', 'meta', 'link', 'hr', 'source', 'col', 'area', 'base', 'wbr', 'path', 'circle', 'rect', 'line', 'polyline', 'polygon', 'ellipse', 'use', 'stop'}
  def __init__(self):
    super().__init__(); self.stack = []; self.errors = []; self.ids = []; self.links = []
    self.quiz = None; self.quizzes = []; self.exercises = []
  def handle_starttag(self, tag, attrs):
    a = dict(attrs)
    if a.get('id'): self.ids.append(a['id'])
    if tag == 'a' and a.get('href'): self.links.append(a['href'])
    if tag in ('link', 'script', 'img') and (a.get('href') or a.get('src')): self.links.append(a.get('href') or a.get('src'))
    cls = (a.get('class') or '').split()
    if 'quiz' in cls and tag == 'div':
      self.quiz = {'answer': a.get('data-answer'), 'fill': a.get('data-fill'), 'keys': [], 'hint': False, 'why': False, 'q': False, 'line': self.getpos()[0]}
      self.quizzes.append(self.quiz)
    if self.quiz is not None:
      if tag == 'button' and a.get('data-k'): self.quiz['keys'].append(a['data-k'])
      if 'hint' in cls: self.quiz['hint'] = True
      if 'why' in cls: self.quiz['why'] = True
      if 'q' in cls: self.quiz['q'] = True
    if 'exercise' in cls and a.get('data-ex'): self.exercises.append((a['data-ex'], a.get('data-ex-py'), self.getpos()[0]))
    if tag not in self.VOID: self.stack.append((tag, 'quiz' in cls))
  def handle_startendtag(self, tag, attrs): pass
  def handle_endtag(self, tag):
    if tag in self.VOID: return
    if not self.stack: self.errors.append(f'stray </{tag}> at line {self.getpos()[0]}'); return
    if self.stack[-1][0] != tag:
      # find it further down (implicitly closed p/li are legal HTML)
      names = [t for t, _ in self.stack]
      if tag in names:
        while self.stack and self.stack[-1][0] != tag:
          t, _ = self.stack.pop()
          if t not in ('p', 'li', 'td', 'th', 'tr', 'option', 'dt', 'dd'): self.errors.append(f'<{t}> closed by </{tag}> at line {self.getpos()[0]}')
      else:
        self.errors.append(f'stray </{tag}> at line {self.getpos()[0]}'); return
    t, isq = self.stack.pop()
    if isq: self.quiz = None

pages = sorted(glob.glob(os.path.join(SITE, '**', '*.html'), recursive=True))
pages = [p for p in pages if 'vendor' not in p]
nq = nex = 0
for p in pages:
  rel = os.path.relpath(p, ROOT).replace('\\', '/')
  src = open(p, encoding='utf-8').read()
  body = re.sub(r'<script\b.*?</script>', '', src, flags=re.S)
  pr = P(); pr.feed(body)
  for e in pr.errors[:5]: problems.append(f'{rel}: html {e}')
  dup = {i for i in pr.ids if pr.ids.count(i) > 1}
  if dup: problems.append(f'{rel}: duplicate ids {sorted(dup)}')
  for q in pr.quizzes:
    nq += 1
    where = f'{rel}:{q["line"]}'
    if not q['q']: problems.append(f'{where}: quiz without p.q')
    if not q['hint']: problems.append(f'{where}: quiz without a hint')
    if not q['why']: problems.append(f'{where}: quiz without a .why')
    if q['answer']:
      if q['answer'] not in q['keys']: problems.append(f'{where}: data-answer {q["answer"]} is not one of the options {q["keys"]}')
      if len(set(q['keys'])) != len(q['keys']): problems.append(f'{where}: duplicate option keys {q["keys"]}')
    elif q['fill'] is None: problems.append(f'{where}: quiz has neither data-answer nor data-fill')
    elif not q['fill'].strip(): problems.append(f'{where}: empty data-fill')
  for ex, py, line in pr.exercises:
    nex += 1
    for i in (ex, py):
      if i and not os.path.exists(os.path.join(ROOT, 'exercises', i + '.json')): problems.append(f'{rel}:{line}: exercise {i} has no JSON')
  for href in pr.links:
    if re.match(r'(https?:|mailto:|#|data:|javascript:)', href): continue
    target = href.split('#')[0].split('?')[0]
    if not target: continue
    path = os.path.normpath(os.path.join(os.path.dirname(p), target))
    if not os.path.exists(path): problems.append(f'{rel}: broken link {href}')

# every exercise JSON is used on a page, and its solution exists
used = set()
for p in pages:
  used |= set(re.findall(r'data-ex(?:-py)?="([^"]+)"', open(p, encoding='utf-8').read()))
EXT = {'ocaml': 'ml', 'c': 'c', 'uir': 'uir', 'python': 'py'}
for j in glob.glob(os.path.join(ROOT, 'exercises', '*.json')):
  d = json.load(open(j, encoding='utf-8'))
  if d['id'] not in used: problems.append(f'exercise {d["id"]} is not on any page')
  if not os.path.exists(os.path.join(ROOT, '_reference', 'solutions', f'{d["id"]}.{EXT[d["lang"]]}')): problems.append(f'exercise {d["id"]} has no solution file')
  if d['id'] != os.path.basename(j)[:-5]: problems.append(f'exercise file {j} has id {d["id"]}')

# inline scripts must at least parse: a syntax error silently kills every figure and quiz on the page
node = shutil.which('node')
if node:
  with tempfile.TemporaryDirectory() as d:
    for p in pages:
      for k, js in enumerate(re.findall(r'<script>(.*?)</script>', open(p, encoding='utf-8').read(), re.S)):
        f = os.path.join(d, f's{k}.js'); open(f, 'w', encoding='utf-8').write(js)
        r = subprocess.run([node, '--check', f], capture_output=True, text=True)
        if r.returncode: problems.append(f"{os.path.relpath(p, ROOT)}: inline script {k} doesn't parse: " + (r.stderr.strip().splitlines() or [''])[-1])

print(f'{len(pages)} pages, {nq} quizzes, {nex} exercise blocks')
for x in problems: print('  ' + x)
print('problems:', len(problems))
sys.exit(1 if problems else 0)
