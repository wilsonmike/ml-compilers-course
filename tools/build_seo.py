#!/usr/bin/env python3
# Make the site easy to crawl. Writes, from the pages under site/:
#   sitemap.xml, robots.txt, llms.txt   at the repo root
#   a <!-- seo --> block in each page head: description, canonical URL, Open Graph tags
# Run after adding, renaming or rewording a page: python tools/build_seo.py
import html, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = 'https://sharpterminal.com'
NAME = 'ML compilers, from zero'
REPO = 'https://github.com/wilsonmike/ml-compilers-course'
SECTIONS = {
  'week0': 'Week 0: prerequisites (C, memory, IRs, tensors, matmul, Python or OCaml)',
  'week1': 'Week 1: UOps and rewrites',
  'week2': 'Week 2: memory and rendering C',
  'week3': 'Week 3: loops',
  'week4': 'Week 4: rangeify, reduce, materialization',
  'week5': 'Week 5: movement ops (reshape, permute, pad, shrink, any rank)',
  'week6': 'Week 6: math ops, sugar, autodiff, data files and training on MNIST',
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

def seo_block(p, title, desc):
  a = lambda s: html.escape(s, quote=True)
  u = url(p)
  return ('<!-- seo: written by tools/build_seo.py -->\n'
    f'<meta name="description" content="{a(clip(desc))}">\n'
    f'<link rel="canonical" href="{u}">\n'
    f'<meta property="og:site_name" content="{a(NAME)}">\n'
    f'<meta property="og:type" content="{"website" if p.name == "index.html" and p.parent.name == "site" else "article"}">\n'
    f'<meta property="og:title" content="{a(title)}">\n'
    f'<meta property="og:description" content="{a(clip(desc, 200))}">\n'
    f'<meta property="og:url" content="{u}">\n'
    '<meta name="twitter:card" content="summary">\n'
    '<!-- /seo -->\n')

pages = sorted(ROOT.glob('site/**/*.html'), key=lambda p: (not (p.name == 'index.html' and p.parent.name == 'site'), p.as_posix()))
groups = {}
for p in pages:
  src, title, h1, lede = info(p)
  block = seo_block(p, title, lede)
  src = re.sub(r'<!-- seo: .*?<!-- /seo -->\n', '', src, flags=re.S)
  src = re.sub(r'(<title>.*?</title>\n)', lambda m: m.group(1) + block, src, count=1, flags=re.S)
  p.write_text(src, encoding='utf-8', newline='\n')
  groups.setdefault(p.parent.name, []).append((p, h1, lede))

rows = ''.join(f'  <url><loc>{url(p)}</loc></url>\n' for p in pages)
(ROOT / 'sitemap.xml').write_text(
  '<?xml version="1.0" encoding="UTF-8"?>\n'
  '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + '</urlset>\n', encoding='utf-8', newline='\n')

(ROOT / 'robots.txt').write_text(
  'User-agent: *\nDisallow: /_reference/\nAllow: /\n\n'
  f'Sitemap: {BASE}/sitemap.xml\n', encoding='utf-8', newline='\n')

# llms.txt, in the format of https://llmstxt.org
out = [f'# {NAME}', '',
  '> A free, open-source course where you build a machine learning compiler from scratch, in Python or OCaml. '
  'It is inspired by the public syllabus of CMU 10-411, Compilers for Machine Learning, and is independent: '
  'not affiliated with CMU or George Hotz.', '',
  'The compiler works on a small graph IR of UOps, written in a text format called .uir. Each week adds ops and '
  'a spec, and a test suite grades your compiler against a reference implementation. Week 0 teaches the '
  'prerequisites (C, memory and caches, IRs, tensors, matmul, and the language you write the compiler in). '
  'Every lesson has quizzes with hints and answers, and graded exercises that run in the browser editor.', '',
  f'Source code, tests and the reference compiler: {REPO}', '']
for key, title in [('site', 'Start here')] + list(SECTIONS.items()):
  if key not in groups: continue
  out += [f'## {title}', '']
  out += [f'- [{h1}]({url(p)})' + (f': {clip(lede, 200)}' if lede else '') for p, h1, lede in groups[key]]
  out.append('')
out += ['## Specs', '', 'The .uir format, one plain Markdown file per week.', '']
out += [f'- [.uir week {n}]({BASE}/spec/uir-week{n}.md)' for n in range(1, 7)]
out += ['', '## Optional', '',
  f'- [GitHub repository]({REPO}): the course pages, exercises, tests and the Python reference compiler',
  '- [10-411 course site](https://10-411.com/): the CMU course this one follows', '']
(ROOT / 'llms.txt').write_text('\n'.join(out), encoding='utf-8', newline='\n')
print(f'{len(pages)} pages: sitemap.xml, robots.txt, llms.txt and page heads written')
