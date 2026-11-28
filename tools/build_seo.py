#!/usr/bin/env python3
# Make the site easy to crawl. Writes, from the pages under site/:
#   sitemap.xml, robots.txt, llms.txt   at the repo root
#   a <!-- seo --> block in each page head: description, canonical URL, Open Graph tags
# Run after adding, renaming or rewording a page: python tools/build_seo.py
import hashlib, html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = 'https://sharpterminal.com'
NAME = 'ML Compilers, From Zero'
BRAND = 'Sharp Terminal'
REPO = 'https://github.com/wilsonmike/ml-compilers-course'
SECTIONS = {
  'start': 'Start: run a program, then write the interpreter that runs it',
  'learn': 'Learn Python, Learn OCaml, and hard ideas explained slowly',
  'week0': 'Week 0: short primers, each placed just before the week that needs it (C, memory, IRs, tensors, matmul, Python or OCaml setup)',
  'week1': 'Week 1: UOps and rewrites',
  'week2': 'Week 2: memory and rendering C',
  'week3': 'Week 3: loops',
  'week4': 'Week 4: rangeify, reduce, materialization',
  'week5': 'Week 5: movement ops (reshape, permute, pad, shrink, any rank)',
  'week6': 'Week 6: math ops, sugar, autodiff, data files and training on MNIST',
  'week7': 'Week 7: fast kernels (measuring speed, tiling, upcast, threads)',
  'week8': 'Week 8: GPUs (blocks and threads, shared memory, rendering CUDA, getting a GPU)',
  'week9': 'Week 9: GPUs, part 2 (registers, fast GEMMs, tensor cores, convolutions, flash attention)',
  'week10': 'Week 10: multiple GPUs (device loops, shards, moving memory, a sharded GEMM, training on several GPUs)',
  'resources': 'Resources',
}

def url(p):
  # Cloudflare Pages serves /x.html as /x and /dir/index.html as /dir/
  rel = p.relative_to(ROOT).as_posix()
  if rel.endswith('index.html'): rel = rel[:-len('index.html')]
  elif rel.endswith('.html'): rel = rel[:-len('.html')]
  return f'{BASE}/{rel}'

def text(s):
  return ' '.join(html.unescape(re.sub(r'<[^>]+>', '', s)).split())

def clip(s, n=160):
  if len(s) <= n: return s
  return s[:n].rsplit(' ', 1)[0].rstrip(',.:') + '...'

def info(p):
  src = p.read_text(encoding='utf-8')
  h1 = re.search(r'<h1[^>]*>(.*?)</h1>', src, re.S)
  lede = re.search(r'<p class="lede"[^>]*>(.*?)</p>', src, re.S)
  title = re.search(r'<title>(.*?)</title>', src, re.S)
  return src, text(title.group(1)), text(h1.group(1)) if h1 else text(title.group(1)), text(lede.group(1)) if lede else ''

ASSETS = ROOT / 'site' / 'assets'
WORKER = hashlib.sha256((ASSETS / 'py-worker.js').read_bytes()).hexdigest()[:10]
_js = (ASSETS / 'course.js').read_bytes()
_js2 = re.sub(rb"assets/py-worker\.js(?:\?v=[0-9a-f]+)?'", f"assets/py-worker.js?v={WORKER}'".encode(), _js)
if _js2 != _js: (ASSETS / 'course.js').write_bytes(_js2)
VERSION ={n: hashlib.sha256((ASSETS / n).read_bytes()).hexdigest()[:10] for n in ('course.css', 'course.js')}
PRELOAD = ('geist-latin.woff2', 'geist-mono-latin.woff2')

def up(p):
  return '../' * (len(p.relative_to(ROOT / 'site').parts) - 1)

def stamp(src):
  return re.sub(r'((?:href|src)="(?:/site/|(?:\.\./)*)assets/(course\.(?:css|js)))(?:\?v=[0-9a-f]+)?"',
                lambda m: f'{m.group(1)}?v={VERSION[m.group(2)]}"', src)

def seo_block(p, title, desc):
  a = lambda s: html.escape(s, quote=True)
  u = url(p)
  return ('<!-- seo: written by tools/build_seo.py -->\n'
    f'<meta name="description" content="{a(clip(desc))}">\n'
    f'<link rel="canonical" href="{u}">\n'
    f'<meta property="og:site_name" content="{a(BRAND)}">\n'
    f'<meta property="og:type" content="{"website" if p.name == "index.html" and p.parent.name == "site" else "article"}">\n'
    f'<meta property="og:title" content="{a(title)}">\n'
    f'<meta property="og:description" content="{a(clip(desc, 200))}">\n'
    f'<meta property="og:url" content="{u}">\n'
    '<meta name="twitter:card" content="summary">\n'
    f'<link rel="icon" href="{up(p)}assets/icon.svg" type="image/svg+xml">\n'
    f'<link rel="apple-touch-icon" href="{up(p)}assets/apple-touch-icon.png">\n'
    '<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">\n'
    '<meta name="theme-color" content="#09090b" media="(prefers-color-scheme: dark)">\n'
    + ''.join(f'<link rel="preload" href="{up(p)}vendor/fonts/{f}" as="font" type="font/woff2" crossorigin>\n' for f in PRELOAD)
    + (course_ld(u, desc) if p.name == 'index.html' and p.parent.name == 'site' else '')
    + '<!-- /seo -->\n')

def course_ld(u, desc):
  data = [{'@context': 'https://schema.org', '@type': 'WebSite', 'name': BRAND, 'alternateName': NAME, 'url': u},
          {'@context': 'https://schema.org', '@type': 'Course', 'name': NAME, 'description': clip(desc, 300), 'url': u,
           'inLanguage': 'en', 'isAccessibleForFree': True, 'educationalLevel': 'Beginner to advanced',
           'teaches': 'Building a machine learning compiler from scratch in Python or OCaml: graph IRs, rewrites, loops, memory, rendering C and CUDA, autodiff, fast CPU and GPU kernels, tensor cores and multiple GPUs',
           'audience': {'@type': 'Audience', 'audienceType': 'Beginners, Python programmers, systems programmers and machine learning engineers'},
           'provider': {'@type': 'Organization', 'name': BRAND, 'url': BASE + '/'},
           'offers': {'@type': 'Offer', 'category': 'Free', 'price': 0, 'priceCurrency': 'USD'},
           'hasCourseInstance': {'@type': 'CourseInstance', 'courseMode': 'Online'},
           'license': REPO + '/blob/main/LICENSE-CONTENT.md'}]
  return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>\n'

pages = sorted(ROOT.glob('site/**/*.html'), key=lambda p: (not (p.name == 'index.html' and p.parent.name == 'site'), p.as_posix()))
groups = {}
for p in pages:
  src, title, h1, lede = info(p)
  block = seo_block(p, title, lede)
  src = re.sub(r'<!-- seo: .*?<!-- /seo -->\n', '', src, flags=re.S)
  src = re.sub(r'(<title>.*?</title>\n)', lambda m: m.group(1) + block, src, count=1, flags=re.S)
  src = stamp(src)
  p.write_text(src, encoding='utf-8', newline='\n')
  groups.setdefault(p.parent.name, []).append((p, h1, lede))
f404 = ROOT / '404.html'
if f404.exists(): f404.write_text(stamp(f404.read_text(encoding='utf-8')), encoding='utf-8', newline='\n')

rows = ''.join(f'  <url><loc>{url(p)}</loc></url>\n' for p in pages)
(ROOT / 'sitemap.xml').write_text(
  '<?xml version="1.0" encoding="UTF-8"?>\n'
  '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + '</urlset>\n', encoding='utf-8', newline='\n')

(ROOT / 'robots.txt').write_text(
  'User-agent: *\nDisallow: /_reference/\nDisallow: /api/\nAllow: /\n\n'
  f'Sitemap: {BASE}/sitemap.xml\n', encoding='utf-8', newline='\n')

# llms.txt, in the format of https://llmstxt.org
out = [f'# {NAME}, by {BRAND}', '',
  '> A free, open-source, self-paced course where you build a machine learning compiler from scratch, in Python or OCaml. '
  'It is inspired by the public syllabus of CMU 10-411, Compilers for Machine Learning, and is independent: '
  'not affiliated with CMU or George Hotz.', '',
  'The compiler works on a small graph IR of UOps, written in a text format called .uir. Each week adds ops and '
  'a spec, and each week ends in a hands-on lab where a test suite grades your compiler against a reference implementation. '
  'It starts with two short steps (run a program, then write the interpreter that runs it) and goes through ten weeks: '
  'interpreting and simplifying, memory and rendering C, loops, tensors and shapes, autodiff and training on MNIST, fast CPU '
  'kernels, CUDA GPU kernels, tensor cores and flash attention, and running on several GPUs. Short primers on C, memory, '
  'tensors and matrix multiply appear just before the week that needs them, and complete beginners can learn Python or OCaml '
  'from scratch first. Every lesson asks you to guess before it explains, has quizzes with hints and answers, and has graded '
  'exercises that run in the browser editor. No GPU is needed: CUDA runs in an emulator.', '',
  f'Source code, tests and the reference compiler: {REPO}', '']
for key, title in [('site', 'Start here')] + list(SECTIONS.items()):
  if key not in groups: continue
  out += [f'## {title}', '']
  out += [f'- [{h1}]({url(p)})' + (f': {clip(lede, 200)}' if lede else '') for p, h1, lede in groups[key]]
  out.append('')
out += ['## Specs', '', 'The .uir format, one plain Markdown file per week.', '']
out += [f'- [.uir week {n}]({BASE}/spec/uir-week{n}.md)' for n in range(1, 11)]
out += ['', '## Optional', '',
  f'- [GitHub repository]({REPO}): the course pages, exercises, tests and the Python reference compiler',
  '- [10-411 course site](https://10-411.com/): the CMU course this one follows', '']
(ROOT / 'llms.txt').write_text('\n'.join(out), encoding='utf-8', newline='\n')
print(f'{len(pages)} pages: sitemap.xml, robots.txt, llms.txt and page heads written')
