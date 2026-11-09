#!/usr/bin/env python3
"""Check the site's CSS and pages against the house design and copy rules (the same rules as Behavior's
scripts/design-lint.ts and copy-lint.ts, minus the parts that are Behavior's own, such as its fonts).

  python tools/design_lint.py            # counts per file, exits 1 on any finding
  python tools/design_lint.py --list     # every finding

A line can opt out with a `design-ok` or `copy-ok` comment saying why.
"""
import os, re, sys, glob, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ACCENTS = r'(?:accent|good|bad|warn)'
CSS_RULES = [
  ('small-text', re.compile(r'font-size:\s*(?:0?\.(?:[0-7]\d*|8(?:[0-6]\d*)?)rem|(?:[0-9]|1[0-3])(?:\.\d+)?px)|font:\s*(?:italic\s+)?(?:\d{3}\s+)?(?:0?\.(?:[0-7]\d*|8(?:[0-6]\d*)?)rem|(?:[0-9]|1[0-3])(?:\.\d+)?px)(?![\w.])'), 'text under 14px (.875rem)'),
  ('weight', re.compile(r'font-weight:\s*(?!(?:400|500|600|inherit|normal|var)\b)[\w.]+|font:\s*(?:italic\s+)?(?!(?:400|500|600|var|inherit)\b)(\d{3})\b'), 'weight other than 400, 500, or 600'),
  ('pill', re.compile(r'border-radius:\s*(?:999|99|100|9999)(?:px|rem)'), 'pill radius'),
  ('upper', re.compile(r'text-transform:\s*uppercase'), 'all-caps label (use sentence case)'),
  ('tracking', re.compile(r'letter-spacing:\s*(?:0?\.0[3-9]|0?\.[1-9])\d*em|letter-spacing:\s*[1-9]\d*(?:\.\d+)?px'), 'wide letter-spacing'),
  ('tint', re.compile(r'var\(--' + ACCENTS + r'-soft\)|color-mix\([^)]*var\(--' + ACCENTS), 'tinted fill from accent, good, bad, or warn (use type, an ink outline, or a mark)'),
  # Status colours (good, bad, warn) may frame a status cell, as words and marks do. The accent may not.
  ('accent-ui', re.compile(r'background(?:-color)?:\s*var\(--accent\)|border-color:\s*var\(--accent\)|border(?:-\w+)?:\s*\d+px\s+\w+\s+var\(--accent'), 'accent as a fill or border on UI (selections are ink)'),
  ('edge-bar', re.compile(r'border-(?:left|inline-start)(?:-color)?:[^;]*var\(--' + ACCENTS + r'\)|box-shadow:[^;]*inset\s+-?[1-9]\d*(?:\.\d+)?px\s+0(?:px)?(?:\s+0(?:px)?)?(?:\s+0(?:px)?)?\s+var\(--' + ACCENTS + r'\)'), 'coloured edge bar as a highlight'),
  ('dashed', re.compile(r'border(?:-\w+)?:[^;]*\bdashed\b|border-style:\s*dashed'), 'dashed border'),
  ('wrap-shorthand', re.compile(r'text-wrap:\s*(?:balance|pretty|stable)'), 'text-wrap shorthand resets nowrap (use text-wrap-style)'),
  ('glow', re.compile(r'(?:box|text)-shadow:[^;]*var\(--' + ACCENTS + r'\)|drop-shadow\('), 'glow'),
  ('gradient', re.compile(r'(?:linear|radial|conic)-gradient\('), 'gradient'),
]
HEX = re.compile(r'(?<![\w&-])#(?:[0-9a-f]{8}|[0-9a-f]{6}|[0-9a-f]{3,4})\b', re.I)
RGB = re.compile(r'rgba?\(\s*\d+[\s,]+\d+[\s,]+\d+', re.I)
SLOP = ['unlock', 'unlocks', 'seamless', 'seamlessly', 'supercharge', 'elevate', 'elevates', 'delve', 'delves', 'empower', 'empowers', 'robust',
  'leverage', 'leverages', 'leveraging', "in today's", 'game-changer', 'game-changing', 'cutting-edge', 'revolutionize', 'effortless', 'effortlessly',
  'streamline', 'unleash', 'next-level', 'world-class', 'best-in-class', 'synergy', 'holistic', 'dive into', 'deep dive', 'transformative',
  'look no further', 'navigate the', 'ever-evolving', 'fast-paced', 'tapestry', 'embark', 'in the realm of', 'skyrocket', 'turbocharge', 'demystify', 'master the']
SLOP_RE = re.compile(r'(?<![\w-])(?:' + '|'.join(re.escape(w) for w in SLOP) + r')(?![\w-])', re.I)

def css_findings(path, text):
  out, depth_token = [], False
  for n, line in enumerate(text.split('\n'), 1):
    if 'design-ok' in line: continue
    s = re.sub(r'/\*.*?\*/', '', line)
    # Token blocks (:root and the dark theme) are the one place raw colours belong.
    if re.match(r'\s*(?:@media[^{]*\{\s*)?:root', s): depth_token = True
    if not depth_token:
      if (HEX.search(s) or RGB.search(s)) and not re.search(r'url\(|data:|%23', s): out.append((n, 'raw-colour', 'raw colour outside the tokens', line))
      for rule, rx, say in CSS_RULES:
        if rx.search(s): out.append((n, rule, say, line))
    if depth_token and '}' in s and not re.search(r'\{[^}]*$', s): depth_token = False
  return out

def visible_text(markup):
  markup = re.sub(r'<(script|style|pre|svg|textarea)\b.*?</\1>', ' ', markup, flags=re.S | re.I)
  # Inline code is a word in the sentence, so a semicolon right after it still counts.
  markup = re.sub(r'<code\b.*?</code>', 'x', markup, flags=re.S | re.I)
  markup = re.sub(r'<[^>]+>', ' ', markup)
  return html.unescape(markup)

def html_findings(path, text):
  out, block = [], None
  for n, line in enumerate(text.split('\n'), 1):
    low = line.lower()
    # Lines inside <style>, <script>, and <pre> blocks are not prose. <style> lines follow the CSS rules.
    opened = re.search(r'<(style|script|pre)\b', low)
    if block is None and opened and f'</{opened.group(1)}>' not in low[opened.end():]: block = opened.group(1); continue
    if block:
      if f'</{block}>' in low: block = None
      elif block == 'style' and 'design-ok' not in line:
        for rule, rx, say in CSS_RULES:
          if rx.search(line): out.append((n, rule, say, line))
        if (HEX.search(line) or RGB.search(line)) and not re.search(r'url\(|data:|%23', line): out.append((n, 'raw-colour', 'raw colour outside the tokens', line))
      continue
    if 'copy-ok' in line or 'design-ok' in line: continue
    for m in re.finditer(r'style="([^"]*)"', line):
      for rule, rx, say in CSS_RULES:
        if rx.search(m.group(1)): out.append((n, rule, say, line))
    t = visible_text(line)
    if '\u2014' in t: out.append((n, 'em-dash', 'em dash (use a comma, a period, or "and")', line))
    if re.search(r'[a-z)\'"’”]; +[a-zA-Z]', t): out.append((n, 'semicolon', 'semicolon inside a sentence (make two sentences)', line))
    m = SLOP_RE.search(t)
    if m: out.append((n, 'slop', f'AI-slop word ("{m.group(0)}")', line))
  return out

def main():
  sys.stdout.reconfigure(encoding='utf-8')
  listing = '--list' in sys.argv
  files = glob.glob(os.path.join(ROOT, 'site', 'assets', '*.css')) + glob.glob(os.path.join(ROOT, 'site', '**', '*.html'), recursive=True) + glob.glob(os.path.join(ROOT, '*.html'))
  total, by = 0, {}
  for f in sorted(files):
    if 'vendor' in f.replace('\\', '/').split('/'): continue
    text = open(f, encoding='utf-8').read()
    found = css_findings(f, text) if f.endswith('.css') else html_findings(f, text)
    if found: by[os.path.relpath(f, ROOT)] = found; total += len(found)
  for f, fs in sorted(by.items(), key=lambda kv: -len(kv[1])):
    rules = {}
    for _, r, _, _ in fs: rules[r] = rules.get(r, 0) + 1
    print(f'{len(fs):5}  {f}  ({", ".join(f"{r} {c}" for r, c in rules.items())})')
    if listing:
      for n, r, say, line in fs: print(f'         {n}: {say}: {line.strip()[:140]}')
  if total: print(f'\n{total} findings in {len(by)} files'); sys.exit(1)
  print('No design or copy findings.')

if __name__ == '__main__': main()
