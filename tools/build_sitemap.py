#!/usr/bin/env python3
# Write sitemap.xml and robots.txt at the repo root, listing every page under site/.
# Run after adding or renaming a page: python tools/build_sitemap.py
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = 'https://sharpterminal.com'

def url(p):
  # Cloudflare Pages serves /x.html as /x and /dir/index.html as /dir/
  rel = p.relative_to(ROOT).as_posix()
  if rel.endswith('index.html'): rel = rel[:-len('index.html')]
  elif rel.endswith('.html'): rel = rel[:-len('.html')]
  return f'{BASE}/{rel}'

pages = sorted(ROOT.glob('site/**/*.html'), key=lambda p: (p.name != 'index.html' or p.parent.name != 'site', p.as_posix()))
rows = ''.join(f'  <url><loc>{url(p)}</loc></url>\n' for p in pages)
(ROOT / 'sitemap.xml').write_text(
  '<?xml version="1.0" encoding="UTF-8"?>\n'
  '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + '</urlset>\n', encoding='utf-8')
(ROOT / 'robots.txt').write_text(
  'User-agent: *\nDisallow: /_reference/\nAllow: /\n\n'
  f'Sitemap: {BASE}/sitemap.xml\n', encoding='utf-8')
print(f'{len(pages)} pages in sitemap.xml')
