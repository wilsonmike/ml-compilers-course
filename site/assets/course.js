// course.js: the app shell (sidebar tree, top bar, theme), DAG drawing, steppers, quizzes, and
// LeetCode-style exercises (CodeMirror 5 with vim / emacs / sublime keymaps, graded by tools/serve.py).
// A page sets <body data-root="../"> and puts its content in <main>; everything else is built here.
const CC = (() => {
  const h = (tag, attrs = {}, ...kids) => {
    const svg = ['svg', 'g', 'rect', 'text', 'path', 'line', 'circle', 'marker', 'defs', 'polygon', 'tspan', 'title'].includes(tag);
    const e = svg ? document.createElementNS('http://www.w3.org/2000/svg', tag) : document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) if (v != null) k === 'text' ? (e.textContent = v) : k.startsWith('on') ? (e[k] = v) : e.setAttribute(k, v);
    for (const k of kids.flat()) if (k != null) e.append(k);
    return e;
  };
  const store = { get: k => { try { return localStorage.getItem(k); } catch { return null; } },
                  set: (k, v) => { try { localStorage.setItem(k, v); } catch {} } };

  // ---- the one table of contents ----
  const NAV = [
    { title: 'Start here', items: [['index.html', 'Overview']] },
    { title: 'Resources', items: [['resources/index.html', 'All resources'], ['resources/debugging.html', 'Debugging your compiler'],
      ['resources/review.html', 'Quiz review'], ['resources/glossary.html', 'Glossary'], ['resources/languages.html', 'Python and OCaml, deeper']] },
    { title: 'Week 0 · Prerequisites', items: [
      ['week0/01-c-and-pointers.html', 'C and pointers', '0.1'], ['week0/02-memory-and-caches.html', 'Memory and caches', '0.2'],
      ['week0/03-compilers-and-irs.html', 'Compilers and IRs', '0.3'], ['week0/04-tensors-and-shapes.html', 'Tensors and shapes', '0.4'],
      ['week0/05-matmul.html', 'Matrix multiply', '0.5'], ['week0/06-ocaml.html', 'OCaml crash course', '0.6'],
      ['week0/07-python.html', 'Python for this course', '0.7']] },
    { title: 'Week 1 · UOps and rewrites', items: [
      ['week1/01-the-uop.html', 'The UOp', '1.1'], ['week1/02-uir-and-interpreting.html', '.uir and interpreting', '1.2'],
      ['week1/03-rewrites-and-folding.html', 'Rewrites and folding', '1.3'], ['week1/04-symbolic.html', 'Symbolic simplification', '1.4'],
      ['week1/05-call-and-param.html', 'CALL, PARAM, STACK, INDEX', '1.5'], ['week1/06-lab.html', 'Lab: your compiler', '1.6']] },
    { title: 'Week 2 · Memory and rendering C', items: [
      ['week2/01-buffers-and-views.html', 'Buffers and views', '2.1'], ['week2/02-load-store-after.html', 'Load, store, after', '2.2'],
      ['week2/03-bounds.html', 'Proving bounds', '2.3'], ['week2/04-rendering-c.html', 'Rendering C', '2.4'],
      ['week2/05-the-runtime.html', 'The runtime', '2.5'], ['week2/06-lab.html', 'Lab: memory and C', '2.6']] },
    { title: 'Week 3 · Loops', items: [
      ['week3/01-ranges.html', 'Ranges and end', '3.1'], ['week3/02-memory-in-loops.html', 'Memory in loops', '3.2'],
      ['week3/03-gemm.html', 'A matmul by hand', '3.3'], ['week3/04-conv.html', 'A convolution by hand', '3.4'],
      ['week3/05-rendering-loops.html', 'Rendering loops', '3.5'], ['week3/06-lab.html', 'Lab: loops', '3.6']] },
    { title: 'Week 4 · Rangeify', items: [
      ['week4/01-vectors.html', 'Vectors and elementwise ops', '4.1'], ['week4/02-reduce-expand.html', 'Reduce and expand', '4.2'],
      ['week4/03-rangeify.html', 'Rangeify', '4.3'], ['week4/04-materialization.html', 'Fuse or materialize', '4.4'],
      ['week4/05-rendering-vectors.html', 'Rendering vectors', '4.5'], ['week4/06-lab.html', 'Lab: rangeify', '4.6']] },
    { title: 'Week 5 · Movement ops', items: [
      ['week5/01-shapes.html', 'Any rank, flat memory', '5.1'], ['week5/02-reshape-permute.html', 'Reshape and permute', '5.2'],
      ['week5/03-pad-shrink-expand.html', 'Pad, shrink, expand, stack', '5.3'], ['week5/04-matmul-conv.html', 'Matmul and conv from movement', '5.4'],
      ['week5/05-rangeify-movement.html', 'Rangeify movement ops', '5.5'], ['week5/06-lab.html', 'Lab: movement ops', '5.6']] },
    { title: 'Week 6 · Autodiff', items: [
      ['week6/01-math.html', 'Math from adds', '6.1'], ['week6/02-sugar.html', 'Sugar', '6.2'],
      ['week6/03-autodiff.html', 'Automatic differentiation', '6.3'], ['week6/04-gradients-of-shapes.html', 'Gradients through shapes', '6.4'],
      ['week6/05-data-and-mnist.html', 'Data and MNIST', '6.5'], ['week6/06-lab.html', 'Lab: train MNIST', '6.6']] },
  ];
  const ROOT = () => document.body.dataset.root || './';
  // The course's source, linked from the top bar of every page
  const REPO = 'https://github.com/wilsonmike/ml-compilers-course';
  // Google Analytics 4, through the Google tag container (it carries the GA4 stream, G-5W4EDH8RFN). Only on the
  // live site, so local copies and previews never count as visits.
  const TAG_ID = 'GTM-MPMCLH74';
  if (/(^|\.)sharpterminal\.com$/.test(location.hostname)) {
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { dataLayer.push(arguments); };
    gtag('js', new Date());
    const s = document.createElement('script'); s.async = true; s.src = 'https://www.googletagmanager.com/gtm.js?id=' + TAG_ID;
    document.head.append(s);
  }
  const ghLink = () => { const a = h('a', { class: 'gh', href: REPO, title: 'The course on GitHub', 'aria-label': 'The course on GitHub' });
    a.innerHTML = '<svg viewBox="0 0 16 16" width="20" height="20" aria-hidden="true" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>'; return a; };
  // the nav entry for this page: the longest matching path wins, so resources/index.html isn't mistaken for index.html
  // Hosts like Cloudflare Pages serve /week1/01-the-uop.html as /week1/01-the-uop, and /site/index.html as /site/,
  // so put the file name back before matching.
  const here = () => { let p = location.pathname.replace(/\\/g, '/');
    if (p.endsWith('/')) p += 'index.html'; else if (!/\.[a-z0-9]+$/i.test(p.split('/').pop())) p += '.html';
    const hits = NAV.flatMap(g => g.items.map(i => [g, i])).filter(([, i]) => p.endsWith('/' + i[0]) || (i[0] === 'index.html' && /\/site\/?$/.test(p)));
    return hits.sort((a, b) => b[1][0].length - a[1][0].length)[0]; };

  // ---- theme ----
  const theme = () => document.documentElement.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  const savedTheme = store.get('cc-theme'); if (savedTheme) document.documentElement.dataset.theme = savedTheme;
  // ---- language track: the language you write your compiler in. Exercises with a Python version (data-ex-py) and
  // text marked .only-python / .only-ocaml follow it. Python is the default.
  const TRACKS = [['python', 'Python'], ['ocaml', 'OCaml']];
  const track = () => (store.get('cc-track') === 'ocaml' ? 'ocaml' : 'python');
  document.documentElement.dataset.track = track();
  function trackSelect(cls) {
    const s = h('select', { class: cls, 'aria-label': 'Language you write your compiler in', onchange: () => { store.set('cc-track', s.value); location.reload(); } },
      TRACKS.map(([v, t]) => h('option', { value: v, text: t })));
    s.value = track(); return s;
  }
  const TOUCH = matchMedia('(pointer: coarse)').matches || /[?&]touch=1/.test(location.search);
  if (TOUCH) document.documentElement.classList.add('touch');

  // ---- runner (tools/serve.py) ----
  let runnerP = null;
  const runner = () => runnerP ||= (location.protocol.startsWith('http')
    ? fetch(ROOT() + '../api/health', { cache: 'no-store' }).then(r => r.ok ? r.json() : null).catch(() => null) : Promise.resolve(null));
  const api = p => ROOT() + '../api/' + p;

  // ---- shell ----
  function frame() {
    const b = document.body, root = ROOT(), cur = here(), main = document.querySelector('main');
    const prog = href => { try { return JSON.parse(store.get('cc-prog:' + href) || 'null'); } catch { return null; } };
    const item = ([href, title, n]) => { const p = prog(href);
      return h('li', {}, h('a', { href: root + href, class: cur && cur[1][0] === href ? 'on' : null, 'aria-current': cur && cur[1][0] === href ? 'page' : null },
        n ? h('span', { class: 'n', text: n }) : null, h('span', { text: title }),
        p && p.s > 0 ? h('span', { class: 'prog' + (p.s >= p.t ? ' done' : ''), text: p.s >= p.t ? '✓' : `${p.s}/${p.t}` }) : null)); };
    const nav = h('nav', { 'aria-label': 'Lessons' }, NAV.map((g, gi) => {
      if (g.title === 'Start here') return h('ul', { class: 'top' }, g.items.map(item));
      const closed = store.get('cc-grp:' + gi) === '0';
      const grp = h('div', { class: 'grp' + (closed ? ' closed' : '') });
      grp.append(h('button', { type: 'button', 'aria-expanded': String(!closed), onclick: () => {
        const c = grp.classList.toggle('closed'); grp.firstChild.setAttribute('aria-expanded', String(!c)); store.set('cc-grp:' + gi, c ? '0' : '1'); } },
        h('span', { class: 'chev', 'aria-hidden': 'true' }, h('svg', { width: 10, height: 10, viewBox: '0 0 10 10' }, h('path', { d: 'M2 3.5l3 3 3-3', stroke: 'currentColor', 'stroke-width': 1.5, fill: 'none' }))), g.title));
      grp.append(h('ul', {}, g.items.map(item)));
      return grp; }));
    const search = h('input', { type: 'search', placeholder: 'Search lessons', 'aria-label': 'Search lessons', oninput: () => {
      const q = search.value.trim().toLowerCase();
      nav.querySelectorAll('li').forEach(li => (li.hidden = q && !li.textContent.toLowerCase().includes(q)));
      if (q) nav.querySelectorAll('.grp').forEach(g => g.classList.remove('closed')); } });
    const seg = h('div', { class: 'seg', role: 'group', 'aria-label': 'Theme' });
    const paintSeg = () => seg.querySelectorAll('button').forEach(x => x.classList.toggle('on', x.dataset.t === theme()));
    ['light', 'dark'].forEach(t => seg.append(h('button', { type: 'button', 'data-t': t, text: t[0].toUpperCase() + t.slice(1), onclick: () => {
      document.documentElement.dataset.theme = t; store.set('cc-theme', t); paintSeg(); } })));
    paintSeg();
    const km = keymapSelect('sel');
    const side = h('aside', { class: 'side' },
      h('a', { class: 'brand', href: root + 'index.html' }, h('span', { class: 'mark', 'aria-hidden': 'true' }), 'ML compilers, from zero'),
      h('div', { class: 'search' }, search), nav,
      h('div', { class: 'foot' }, h('div', { class: 'row' }, 'Language', trackSelect('sel')), h('div', { class: 'row' }, 'Theme', seg), h('div', { class: 'row' }, 'Editor keys', km)));
    const pill = h('span', { class: 'runner', title: 'Start it with: python tools/serve.py' }, h('span', { class: 'dot' }), 'Runner off');
    runner().then(r => { if (r) { pill.classList.add('on'); pill.lastChild.textContent = 'Runner on'; pill.title = 'Exercises run on your machine via tools/serve.py'; } });
    const crumbs = h('div', { class: 'crumbs' }, cur ? [h('a', { href: root + 'index.html', text: 'Course' }),
      ...(cur[0].title === 'Start here' ? [] : [h('span', { class: 'sep', text: '/' }), cur[0].title.split(' · ')[0]]),
      h('span', { class: 'sep', text: '/' }), cur[1][1]] : []);
    const app = h('div', { class: 'app' });
    const menu = h('button', { class: 'menu', type: 'button', 'aria-label': 'Open lessons', 'aria-expanded': 'false' },
      h('svg', { width: 20, height: 20, viewBox: '0 0 20 20', 'aria-hidden': 'true' }, h('path', { d: 'M3 6h14M3 10h14M3 14h14', stroke: 'currentColor', 'stroke-width': 1.6, fill: 'none' })));
    const scrim = h('div', { class: 'scrim' });
    const page = h('div', { class: 'page' }, h('div', { class: 'docwrap' }, main || ''));
    const wrap = h('div', { class: 'mainwrap' }, h('header', { class: 'topbar' }, menu, crumbs, pill, ghLink()), page);
    app.append(side, scrim, wrap);
    b.prepend(app);
    if (main) toc(main, page);
    document.querySelectorAll('[data-prog]').forEach(a => { const p = prog(a.dataset.prog);
      a.append(h('span', { class: 'p' + (p && p.s >= p.t && p.t ? ' done' : ''), text: p && p.s ? (p.s >= p.t ? 'Done' : `${p.s}/${p.t}`) : '' })); });
    // the drawer is modal on small screens: lock the page behind it, close on Escape or on navigation
    const setOpen = open => { app.classList.toggle('open', open); wrap.inert = open; menu.setAttribute('aria-expanded', String(open)); if (open) (side.querySelector('nav a.on') || side.querySelector('nav a'))?.focus(); };
    menu.onclick = () => setOpen(true); scrim.onclick = () => setOpen(false);
    side.addEventListener('click', e => { if (e.target.closest('a')) setOpen(false); });
    addEventListener('keydown', e => { if (e.key === 'Escape' && app.classList.contains('open')) { setOpen(false); menu.focus(); } });
    matchMedia('(min-width: 901px)').addEventListener('change', e => e.matches && setOpen(false));
  }

  // "On this page": every h2, with the one you're reading highlighted
  function toc(main, page) {
    const hs = [...main.querySelectorAll('h2')];
    if (hs.length < 3) return;
    const used = new Set();
    hs.forEach(x => { if (!x.id) { let id = x.textContent.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'section', k = id, n = 2;
      while (used.has(k) || document.getElementById(k)) k = `${id}-${n++}`; x.id = k; } used.add(x.id); });
    const links = hs.map(x => h('a', { href: '#' + x.id, text: x.textContent }));
    page.classList.add('has-toc');
    page.append(h('aside', { class: 'toc', 'aria-label': 'On this page' }, h('nav', {}, h('span', { class: 'label', text: 'On this page' }), links)));
    const mark = id => links.forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#' + id));
    const seen = new Map();
    const io = new IntersectionObserver(es => { es.forEach(e => seen.set(e.target.id, e.isIntersecting));
      const top = hs.find(x => seen.get(x.id)); if (top) mark(top.id);
      else { const above = hs.filter(x => x.getBoundingClientRect().top < 120).pop(); mark((above || hs[0]).id); } }, { rootMargin: '-60px 0px -55% 0px' });
    hs.forEach(x => io.observe(x));
  }

  // ---- DAG drawing. nodes: [{id, op, sub, src:[id], cls, val, ecls}] ; sources on top, results flow down ----
  function graph(nodes, { width } = {}) {
    const by = new Map(nodes.map(n => [n.id, n])), depth = new Map();
    const d = n => { if (depth.has(n.id)) return depth.get(n.id); depth.set(n.id, 0);
      const v = (n.src || []).length ? 1 + Math.max(...n.src.map(s => d(by.get(s)))) : 0; depth.set(n.id, v); return v; };
    nodes.forEach(d);
    const rows = []; nodes.forEach(n => (rows[depth.get(n.id)] ||= []).push(n));
    const NW = n => Math.max(56, 9 * Math.max(n.op.length, (n.sub || '').length) + 24), NH = n => n.sub ? 50 : 34, GAP = 20, RH = 84;
    const x = new Map();
    const place = row => { let cx = 0; row.forEach(n => { x.set(n.id, cx + NW(n) / 2); cx += NW(n) + GAP; }); return cx - GAP; };
    rows.forEach(place);
    const bary = n => { const s = (n.src || []).map(id => x.get(id)); return s.length ? s.reduce((a, b) => a + b) / s.length : 0; };
    for (let pass = 0; pass < 4; pass++) rows.forEach((row, i) => { if (i) { row.sort((a, b) => bary(a) - bary(b)); place(row); } });
    const W = Math.max(...rows.map(r => place(r)));
    rows.forEach(r => { const w = place(r), off = (W - w) / 2; r.forEach(n => x.set(n.id, x.get(n.id) + off)); });
    const y = n => 12 + depth.get(n.id) * RH;
    const z = parseFloat(getComputedStyle(document.documentElement).fontSize) / 16 || 1;
    const svg = h('svg', { class: 'g', viewBox: `-8 0 ${W + 16} ${rows.length * RH}`, width: Math.round((width || W + 16) * z), role: 'img' });
    const edges = h('g'), ns = h('g');
    nodes.forEach(n => (n.src || []).forEach((s, i) => { const a = by.get(s);
      const x1 = x.get(s), y1 = y(a) + NH(a), x2 = x.get(n.id) + (i - (n.src.length - 1) / 2) * 10, y2 = y(n), m = (y1 + y2) / 2;
      edges.append(h('path', { class: 'edge' + ((n.ecls || [])[i] ? ' ' + n.ecls[i] : ''), d: `M${x1},${y1} C${x1},${m} ${x2},${m} ${x2},${y2}` })); }));
    nodes.forEach(n => { const w = NW(n), X = x.get(n.id) - w / 2, Y = y(n);
      const g = h('g', { class: 'node ' + (n.cls || '') + (n.src && n.src.length ? '' : ' const') });
      g.append(h('rect', { x: X, y: Y, width: w, height: NH(n), rx: 6 }));
      g.append(h('text', { x: x.get(n.id), y: Y + 22, 'text-anchor': 'middle', text: n.op }));
      if (n.sub) g.append(h('text', { class: 'sub', x: x.get(n.id), y: Y + 40, 'text-anchor': 'middle', text: n.sub }));
      if (n.val != null) g.append(h('text', { class: 'val', x: X + w + 6, y: Y + 22, text: '= ' + n.val }));
      if (n.title) g.append(h('title', { text: n.title }));
      ns.append(g); });
    svg.append(edges, ns);
    return svg;
  }

  // ---- tiny .uir -> nodes, hash consed by text: identical (op, src, arg) collapse to one node ----
  function parseUir(text) {
    const names = {}, nodes = [], key = new Map();
    const node = (op, sub, src) => { const k = op + '|' + (sub || '') + '|' + src.join(',');
      if (key.has(k)) return key.get(k); const id = 'n' + nodes.length; nodes.push({ id, op, sub, src }); key.set(k, id); return id; };
    for (let line of text.split('\n')) {
      line = line.split('#')[0].trim(); if (!line) continue;
      const m = line.match(/^%(\w+)\s*=\s*(\w+)\s*(.*)$/); if (!m) continue;
      const toks = m[3].match(/\w+=\[[^\]]*\]|\[[^\]]*\]|\S+/g) || [];
      const src = [], attrs = [];
      for (const t of toks) if (t.includes('=')) attrs.push(t); else if (t.startsWith('%')) src.push(names[t.slice(1)]);
        else if (m[2] === 'const' || m[2] === 'param') attrs.unshift(t); else src.push(node(t, null, []));
      // a literal operand IS a const: "%a = const 2" and a bare "2" are the same hash-consed node
      if (m[2] === 'const' && attrs.length === 1) { names[m[1]] = node(attrs[0], null, []); continue; }
      names[m[1]] = node(m[2], attrs.join(' ') || null, src);
    }
    return { nodes, names };
  }

  // ---- stepper: fig = .fig element; steps = [{caption, ...}]; draw(step, body, i) paints the body ----
  function stepper(fig, steps, draw) {
    const prev = h('button', { class: 'btn', type: 'button', text: 'Prev' }), next = h('button', { class: 'btn primary', type: 'button', text: 'Next' });
    const count = h('span', { class: 'count' }), body = h('div', { class: 'body' }), cap = h('div', { class: 'cap', 'aria-live': 'polite' });
    fig.replaceChildren(h('div', { class: 'head' }, h('span', { class: 'title', text: fig.dataset.title || '' }), h('span', { class: 'ctl' }, count, prev, next)), body, cap);
    let i = 0;
    const show = () => { body.replaceChildren(); draw(steps[i], body, i); cap.innerHTML = steps[i].caption || '';
      count.textContent = `${i + 1} / ${steps.length}`; prev.disabled = i === 0; next.disabled = i === steps.length - 1; };
    prev.onclick = () => { if (i > 0) { i--; show(); } }; next.onclick = () => { if (i < steps.length - 1) { i++; show(); } };
    fig.tabIndex = 0; fig.onkeydown = e => { if (e.target !== fig) return; if (e.key === 'ArrowRight') next.onclick(); if (e.key === 'ArrowLeft') prev.onclick(); };
    show();
    return { go: k => { i = k; show(); } };
  }

  function code(text, hl = -1) {
    return h('div', { class: 'code' }, text.replace(/\n$/, '').split('\n').map((l, i) => h('div', { class: i === hl ? 'hl' : null, text: l || ' ' })));
  }

  // ---- quizzes ----
  // Multiple choice: <div class="quiz" data-answer="b"> .opts > button[data-k] ...
  // Fill in:         <div class="quiz" data-fill="42 | 0x2a"> .fill > input + button ...
  // Optional <p class="hint">..</p> (one or more, revealed in order) and <div class="why">..</div> (shown when done).
  // Wrong answers can be retried. The score counts first-try answers; "Show answer" never counts as right.
  // Every quiz has an id (data-qid, or page + position). A quiz not answered right on the first try is
  // remembered as "missed" until it's answered right first try, so the review page can bring it back.
  // A typed answer matches when it equals an accepted one after trimming and lowercasing, or when both read
  // as the same number (12 and 12.0, 0x40000000 and 1073741824, -inf and −inf), or as the same list
  // once brackets and commas are dropped ((4, 3), [4 3] and 4 by 3).
  function fillMatch(accepted, typed) {
    const norm = x => x.trim().toLowerCase().replace(/\s+/g, ' ').replace(/−/g, '-');
    const num = x => {
      if (/^[-+]?(inf|infinity)$/.test(x)) return x.startsWith('-') ? -Infinity : Infinity;
      if (/^[-+]?0x[0-9a-f]+$/.test(x)) return (x.startsWith('-') ? -1 : 1) * parseInt(x.replace(/^[-+]/, ''), 16);
      return /^[-+]?(\d+\.?\d*|\.\d+)(e[-+]?\d+)?$/.test(x) ? Number(x) : null;
    };
    const t = norm(typed), tn = num(t);
    const flat = x => x.replace(/[\[\]()]/g, ' ').replace(/,|\bby\b/g, ' ').replace(/\s+/g, ' ').trim();   // shapes: (4, 3) = [4 3] = 4 by 3
    return accepted.some(a => { a = norm(a); return a === t || (tn !== null && num(a) === tn) || (flat(a) !== '' && flat(a) === flat(t)); });
  }

  function quizzes(root = document) {
    const all = [...root.querySelectorAll('.quiz')]; let first = 0, done = 0;
    const page = here(); const pageKey = page ? page[1][0] : location.pathname;
    all.forEach((q, i) => { if (!q.dataset.qid) q.dataset.qid = `${pageKey}#${i}`; });
    // the score counts only quizzes on the reader's language track (ids above still index every quiz, so they stay stable)
    const n = all.filter(q => !q.closest(track() === 'python' ? '.only-ocaml' : '.only-python')).length;
    const tally = () => document.querySelectorAll('.score').forEach(s => (s.textContent = `${first} / ${n} first try` + (done < n ? ` · ${n - done} to go` : '')));
    all.forEach(q => {
      const hints = [...q.querySelectorAll('.hint')]; let tries = 0, seen = 0, nudged = false;
      const msg = h('span', { class: 'qmsg', 'aria-live': 'polite' });
      const hintB = hints.length ? h('button', { class: 'btn', type: 'button', text: hints.length > 1 ? `Hint 1 of ${hints.length}` : 'Hint' }) : null;
      const showB = h('button', { class: 'btn quiet', type: 'button', text: 'Show answer' });
      const bar = h('div', { class: 'qactions' }, hintB, showB, msg);
      const why0 = q.querySelector('.why'); if (why0) why0.before(bar); else q.append(bar);
      const mc = !!q.dataset.answer, opts = [...q.querySelectorAll('.opts button')];
      const inp = q.querySelector('.fill input'), checkB = q.querySelector('.fill button');
      const ans = mc ? null : (q.dataset.fill || '').split('|').map(x => x.trim().toLowerCase());
      const finish = (how) => {             // how: 'first' | 'later' | 'shown'
        if (q.classList.contains('done')) return;
        q.classList.add('done'); done++; if (how === 'first') first++;
        try { if (how === 'first') localStorage.removeItem('cc-missed:' + q.dataset.qid); else localStorage.setItem('cc-missed:' + q.dataset.qid, '1'); } catch {}
        opts.forEach(o => { o.disabled = true; if (o.dataset.k === q.dataset.answer) o.classList.add('right'); });
        if (inp) { inp.disabled = checkB.disabled = true; if (how === 'shown') inp.value = q.dataset.fill.split('|')[0].trim(); inp.classList.toggle('good', how !== 'shown'); }
        bar.remove(); hints.forEach(x => x.classList.add('shown'));
        const w = q.querySelector('.why') || q.appendChild(h('div', { class: 'why' }));
        w.prepend(h('span', { class: 'verdict ' + (how === 'shown' ? 'shown' : 'ok'), text: how === 'first' ? 'Right.' : how === 'later' ? `Right, on try ${tries + 1}.` : 'Answer shown.' }));
        tally();
      };
      const miss = text => { tries++; msg.textContent = text; msg.className = 'qmsg no'; };
      opts.forEach(b => { b.type = 'button'; b.onclick = () => {
        if (b.dataset.k === q.dataset.answer) return finish(tries ? 'later' : 'first');
        b.classList.add('wrong'); b.disabled = true; miss(hints.length && seen < hints.length ? 'Not quite. Try another, or take a hint.' : 'Not quite. Try another.'); }; });
      if (inp) { const check = () => { if (q.classList.contains('done') || !inp.value.trim()) return;
          if (fillMatch(ans, inp.value)) return finish(tries ? 'later' : 'first');
          inp.classList.add('bad'); miss(`Not quite${inp.value.trim().length < 40 ? ': ' + inp.value.trim() + ' isn\u2019t it' : ''}. Try again${hints.length && seen < hints.length ? ', or take a hint' : ''}.`); inp.select(); };
        checkB.type = 'button'; checkB.textContent = 'Check'; checkB.onclick = check; inp.onkeydown = e => { if (e.key === 'Enter') check(); };
        inp.oninput = () => inp.classList.remove('bad'); }
      if (hintB) hintB.onclick = () => { hints[seen++].classList.add('shown'); msg.textContent = '';
        if (seen >= hints.length) hintB.remove(); else hintB.textContent = `Hint ${seen + 1} of ${hints.length}`; };
      showB.onclick = () => {
        if (seen < hints.length && !nudged) { nudged = true; showB.textContent = 'Show answer anyway'; msg.textContent = 'Stuck? A hint might be all you need.'; msg.className = 'qmsg'; return; }
        finish('shown'); };
    });
    tally();
  }

  // `code` in hint and explanation text becomes <code>; everything else is plain text
  const rich = t => { const e = h('span'); String(t).split(/(`[^`]+`)/).forEach(part => e.append(part.startsWith('`') && part.endsWith('`') && part.length > 1 ? h('code', { text: part.slice(1, -1) }) : part)); return e; };

  // ---- exercises ----
  const KEYMAPS = [['default', 'Default'], ['vim', 'Vim'], ['emacs', 'Emacs'], ['sublime', 'Sublime']];
  const editors = new Set(), selects = new Set();
  const keymap = () => store.get('cc-keymap') || 'default';
  function setKeymap(k) { store.set('cc-keymap', k); editors.forEach(cm => { cm.setOption('keyMap', k); cm.getWrapperElement().dispatchEvent(new Event('cc-keymap')); }); selects.forEach(s => (s.value = k)); }
  function keymapSelect(cls) {
    const s = h('select', { class: cls, 'aria-label': 'Editor key bindings', onchange: () => setKeymap(s.value) }, KEYMAPS.map(([v, t]) => h('option', { value: v, text: t })));
    s.value = keymap(); selects.add(s); return s;
  }
  let cmP = null;
  function loadCM() {
    if (cmP) return cmP;
    const base = ROOT() + 'vendor/codemirror/';
    ['codemirror.css', 'dialog.css'].forEach(f => document.head.append(h('link', { rel: 'stylesheet', href: base + f })));
    const js = f => new Promise((ok, no) => document.head.append(h('script', { src: base + f, onload: ok, onerror: () => no(new Error(f)) })));
    return cmP = js('codemirror.js')
      .then(() => Promise.all(['searchcursor.js', 'dialog.js', 'matchbrackets.js', 'closebrackets.js', 'comment.js', 'active-line.js', 'mllike.js', 'clike.js', 'python.js'].map(js)))
      .then(() => Promise.all(['vim.js', 'emacs.js', 'sublime.js'].map(js)))
      .then(() => { window.CodeMirror.defineMode('uir', () => ({ token(s) {
        if (s.match(/#.*/)) return 'comment';
        if (s.match(/%\w+/)) return 'variable-2';
        if (s.match(/\w+=/)) return 'attribute';
        if (s.match(/\b(i32|f32|bool|void)\b/)) return 'type';
        if (s.match(/-?(\d+\.\d*|\.\d+|\d+)(e[-+]?\d+)?|\b(inf|nan|true|false)\b/)) return 'number';
        if (s.match(/[a-z_]+/)) return 'keyword';
        s.next(); return null; }, lineComment: '#' })); return window.CodeMirror; });
  }
  const MODE = { ocaml: 'text/x-ocaml', c: 'text/x-csrc', uir: 'uir', python: 'text/x-python' }, LANG = { ocaml: 'OCaml', c: 'C', uir: '.uir', python: 'Python' };

  async function exercises() {
    const els = [...document.querySelectorAll('.exercise[data-ex]')];
    if (!els.length) return;
    // each exercise in the reader's language: a Python version where the lesson has one
    const pick = e => (track() === 'python' && e.dataset.exPy) || e.dataset.ex;
    const ids = els.map(pick), page = here(), pageKey = page && 'cc-prog:' + page[1][0];
    const record = () => { if (!pageKey) return; const s = ids.filter(i => store.get('cc-solved:' + i)).length, t = ids.length;
      store.set(pageKey, JSON.stringify({ s, t }));
      const a = document.querySelector('.side a.on'); if (!a || !s) return;   // keep the sidebar count live, once something is solved
      const p = a.querySelector('.prog') || a.appendChild(h('span', { class: 'prog' }));
      p.className = 'prog' + (s >= t ? ' done' : ''); p.textContent = s >= t ? '✓' : `${s}/${t}`; };
    record();
    const r = await runner();
    for (const el of els) {
      const id = pick(el), prompt = h('div', { class: 'ex-prompt' }, ...el.childNodes);
      const work = h('div', { class: 'ex-work' });
      el.replaceChildren(prompt, work);
      el.classList.add(el.classList.contains('small') ? 'stack' : 'bleed');
      // With the runner, the exercise comes from it. Without (a hosted copy, or the runner not started), from the
      // static data that tools/build_static.py writes, so the examples, hints, and answer still show.
      let ex;
      try { ex = await fetch(r ? api('exercise/' + id) : ROOT() + 'data/ex/' + id + '.json').then(x => { if (!x.ok) throw new Error(x.status); return x.json(); }); }
      catch (e) { ex = null; if (r) { work.append(h('div', { class: 'ex-offline', text: `Couldn't load exercise "${id}" (${e.message}).` })); continue; } }
      const offline = () => h('div', { class: 'ex-offline' }, h('strong', { text: 'Code runs on your own machine.' }),
        h('p', {}, 'Get the course on your computer (', h('a', { href: REPO + '#taking-the-course', text: 'how' }), '), then start the runner from its folder.'),
        h('pre', {}, h('code', { text: 'python tools/serve.py' })), h('p', {}, 'Then open ', h('code', { text: 'http://127.0.0.1:4111' }), ' and the editor appears here.'));
      if (!ex) { work.append(offline()); continue; }
      // A language version can carry its own prompt (the page's prompt is written for the original language)
      if (ex.prompt) { const body = h('div'); body.innerHTML = ex.prompt; prompt.replaceChildren(h('h3', { text: ex.title }), ...body.childNodes); }
      const solved = h('span', { class: 'pill solved', text: 'Solved', hidden: store.get('cc-solved:' + id) ? null : '' });
      prompt.prepend(h('div', { class: 'ex-tag' }, h('span', { class: 'pill', text: LANG[ex.lang] }), h('span', { class: 'pill', text: `${ex.ntests} tests` }),
        ex.max_ops != null ? h('span', { class: 'pill', text: `At most ${ex.max_ops} op${ex.max_ops === 1 ? '' : 's'}` }) : null, solved));
      if (ex.samples.length) prompt.append(h('div', { class: 'ex-samples' }, ex.samples.map((s, i) => h('div', { class: 'ex-sample' },
        h('span', { class: 'label', text: ex.samples.length > 1 ? `Example ${i + 1}` : 'Example' }),
        h('pre', {}, h('code', { text: s.label || (s.expr != null ? s.expr : `%out(${(s.args || []).join(', ')})`) })),
        h('p', { class: 'ex-expect' }, 'Expected ', h('code', { text: String(s.expect) }))))));
      let cm = null;
      const stuck = stuckPanel(id, ex, () => cm, solved);
      if (stuck) prompt.append(stuck);
      // With the runner (on your computer): Run and Submit grade the code. Without it (the hosted site, a phone): the
      // same editor, and Compare with answer diffs your code against the reference answer. Nothing runs anywhere.
      const edDiv = h('div', { class: 'ex-editor' });
      const out = h('div', { class: 'ex-out' }, h('span', { class: 'hint', text: r ? 'Run checks the examples. Submit runs every test.'
        : 'Write your answer, then compare it with the reference answer. Running the tests needs the course on your computer.' }));
      const mode = h('span'), keys = h('span', { text: r ? 'Ctrl+Enter run · Ctrl+Shift+Enter submit' : 'Ctrl+Enter compare' });
      const runB = h('button', { class: 'btn', type: 'button', text: 'Run' }), subB = h('button', { class: 'btn primary', type: 'button', text: 'Submit' });
      const cmpB = h('button', { class: 'btn primary', type: 'button', text: 'Compare with answer' });
      const resetB = h('button', { class: 'btn', type: 'button', text: 'Reset', title: 'Back to the starter code' });
      work.append(h('div', { class: 'ex-bar' }, h('span', { class: 'lang', text: LANG[ex.lang] }), keymapSelect('sel'), resetB, ...(r ? [runB, subB] : [cmpB])),
        edDiv, h('div', { class: 'ex-status' }, mode, keys), out);
      let CM;
      try { CM = await loadCM(); } catch (e) { edDiv.append(h('div', { class: 'ex-offline', text: 'Editor failed to load: ' + e.message })); continue; }
      const draftKey = 'cc-code:' + id;
      const go = submit => r ? run(submit) : compare();
      cm = CM(edDiv, { value: store.get(draftKey) ?? ex.starter, mode: MODE[ex.lang], keyMap: keymap(), lineNumbers: true, indentUnit: 2, tabSize: 2,
        matchBrackets: true, autoCloseBrackets: true, styleActiveLine: !TOUCH, viewportMargin: Infinity, showCursorWhenSelecting: true,
        spellcheck: false, autocorrect: false, autocapitalize: false, lineWrapping: TOUCH, screenReaderLabel: 'Code editor',
        extraKeys: { 'Ctrl-Enter': () => go(false), 'Cmd-Enter': () => go(false), 'Shift-Ctrl-Enter': () => go(true), 'Shift-Cmd-Enter': () => go(true),
          Tab: c => c.somethingSelected() ? c.indentSelection('add') : c.replaceSelection('  ') } });
      editors.add(cm);
      edDiv.after(keybar(cm, ex.lang, () => go(false), r ? 'Run' : 'Compare'));
      const paintMode = () => (mode.textContent = keymap() === 'vim' ? '-- NORMAL --' : KEYMAPS.find(k => k[0] === keymap())[1] + ' keys');
      cm.on('vim-mode-change', e => (mode.textContent = '-- ' + (e.subMode ? e.subMode : e.mode).toUpperCase() + ' --'));
      cm.getWrapperElement().addEventListener('cc-keymap', paintMode); paintMode();
      cm.on('change', () => store.set(draftKey, cm.getValue()));
      resetB.onclick = () => { cm.setValue(ex.starter); cm.focus(); };
      async function run(submit) {
        runB.disabled = subB.disabled = true; out.replaceChildren(h('span', { class: 'hint', text: submit ? 'Running every test…' : 'Running examples…' }));
        let res;
        try { res = await fetch(api('run'), { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Course-Runner': '1' },
          body: JSON.stringify({ id, code: cm.getValue(), submit }) }).then(x => x.json()); }
        catch (e) { res = { ok: false, error: 'The runner stopped responding. Is tools/serve.py still running?' }; }
        runB.disabled = subB.disabled = false;
        out.replaceChildren(...render(res, submit));
        if (submit && res.ok && res.passed === res.total) { store.set('cc-solved:' + id, '1'); solved.hidden = false; record(); }
      }
      runB.onclick = () => run(false); subB.onclick = () => run(true);
      // Compare shows the answer's code, so the first time it asks once, as Show answer does.
      let warned = !!store.get('cc-peek:' + id);
      function compare() {
        const ans = ex.answer && ex.answer.code;
        if (!ans) { out.replaceChildren(h('span', { class: 'hint', text: 'This exercise has no reference answer to compare with.' })); return; }
        if (!warned) { warned = true; cmpB.textContent = 'Compare anyway';
          out.replaceChildren(h('span', { class: 'hint', text: 'Comparing shows lines of the answer. Try a hint first if you want to keep the puzzle.' })); return; }
        cmpB.textContent = 'Compare again'; store.set('cc-peek:' + id, '1');
        out.replaceChildren(...diffView(cm.getValue(), ans, ex.lang), offlineNote());
      }
      cmpB.onclick = compare;
    }
  }
  // The one line under a compare result: where real checking happens.
  const offlineNote = () => h('p', { class: 'ex-note' }, 'To run the tests, get the course on your computer (',
    h('a', { href: REPO + '#taking-the-course', text: 'how' }), ') and start ', h('code', { text: 'python tools/serve.py' }), '.');
  // A line diff of your code against the answer. Comments are left out, lines are compared without their spacing, and
  // blank lines are skipped, so a starter's comments or formatting alone never show as a difference.
  const COMMENTS = { ocaml: [/\(\*[\s\S]*?\*\)/g], c: [/\/\*[\s\S]*?\*\//g, /\/\/.*$/gm], uir: [/#.*$/gm], python: [/("""|''')[\s\S]*?\1/g, /#.*$/gm] };
  function diffView(mine, answer, lang) {
    const strip = s => (COMMENTS[lang] || []).reduce((t, re) => t.replace(re, ''), s);
    const prep = s => strip(s).replace(/\r/g, '').split('\n').filter(l => l.trim()).map(l => ({ text: l.replace(/\s+$/, ''), key: l.trim().replace(/\s+/g, ' ') }));
    const a = prep(mine), b = prep(answer), n = a.length, m = b.length;
    const L = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1));
    for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) L[i][j] = a[i].key === b[j].key ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
    const rows = []; let i = 0, j = 0;
    while (i < n || j < m) {
      if (i < n && j < m && a[i].key === b[j].key) { rows.push(['same', b[j].text]); i++; j++; }
      else if (i < n && (j >= m || L[i + 1][j] >= L[i][j + 1])) { rows.push(['del', a[i].text]); i++; }   // yours first, as diffs read
      else { rows.push(['add', b[j].text]); j++; }
    }
    const changed = rows.filter(x => x[0] !== 'same').length;
    if (!changed) return [h('p', { class: 'verdict ok', text: 'Your code matches the answer line for line.' })];
    const mark = { same: ' ', add: '+', del: '−' };
    return [
      h('p', { class: 'ex-diff-head' }, h('strong', { text: `${changed} line${changed === 1 ? '' : 's'} differ.` }),
        ' ', h('span', { class: 'muted', text: '− only in yours, + only in the answer. Comments are left out.' })),
      h('div', { class: 'ex-diff', role: 'group', 'aria-label': 'Your code compared with the answer' },
        rows.map(([t, text]) => h('div', { class: 'd-' + t }, h('span', { class: 'm', 'aria-label': t === 'add' ? 'only in the answer' : t === 'del' ? 'only in yours' : null, text: mark[t] }), text || ' '))),
      h('p', { class: 'ex-note', text: 'Different is not wrong. Many correct answers look nothing like this one, and the tests are the real check.' }),
    ];
  }
  // "Stuck?": hints one at a time, then the reference answer with a short why. Progress is remembered per exercise.
  function stuckPanel(id, ex, getCm, solvedPill) {
    const hints = ex.hints || [];
    const key = 'cc-hints:' + id; let seen = Math.min(+(store.get(key) || 0), hints.length), nudged = false;
    const list = h('ol', { class: 'ex-hints' }), msg = h('span', { class: 'qmsg' }), ansBox = h('div', { class: 'ex-answer', hidden: '' });
    const hintB = h('button', { class: 'btn', type: 'button' }), showB = h('button', { class: 'btn quiet', type: 'button', text: 'Show answer' });
    const paint = () => { list.replaceChildren(...hints.slice(0, seen).map(t => h('li', {}, rich(t))));
      hintB.hidden = seen >= hints.length; hintB.textContent = seen ? `Next hint (${seen + 1} of ${hints.length})` : `Hint (1 of ${hints.length})`; };
    hintB.onclick = () => { seen++; store.set(key, String(seen)); msg.textContent = ''; paint(); };
    const reveal = async () => {
      showB.disabled = true; msg.textContent = 'Loading the answer…';
      let sol = ex.answer || null;   // the static data carries the answer; the runner sends it only when asked
      if (!sol) try { sol = await fetch(api('solution/' + id)).then(r => r.json()); } catch { sol = null; }
      showB.disabled = false;
      if (!sol || !sol.code) { msg.textContent = 'Couldn\u2019t load the answer. Is the runner still running?'; return; }
      msg.textContent = ''; showB.hidden = true; hintB.hidden = true; seen = hints.length; paint(); store.set('cc-peek:' + id, '1');
      const load = h('button', { class: 'btn', type: 'button', text: 'Load into editor', onclick: () => { const cm = getCm(); if (cm) { cm.setValue(sol.code); cm.focus(); } } });
      ansBox.replaceChildren(h('span', { class: 'label', text: 'Answer' }), sol.explain ? h('p', {}, rich(sol.explain)) : '',
        h('pre', {}, h('code', { text: sol.code })), getCm() ? h('div', { class: 'row' }, load, h('span', { class: 'muted', text: 'Reset gets your starter back.' })) : '');
      ansBox.hidden = false;
    };
    showB.onclick = () => {
      if (seen < hints.length && !nudged) { nudged = true; showB.textContent = 'Show answer anyway'; msg.textContent = 'Try a hint first? Seeing the answer ends the puzzle.'; return; }
      reveal();
    };
    paint();
    if (store.get('cc-peek:' + id)) reveal();
    return h('div', { class: 'ex-stuck' }, h('span', { class: 'label', text: 'Stuck?' }), list, h('div', { class: 'qactions' }, hints.length ? hintB : null, showB, msg), ansBox);
  }

  // one-tap keys for what phone keyboards bury: brackets, operators, Tab, cursor moves
  const KEYS = {
    c: ['{', '}', '(', ')', '[', ']', ';', '=', '+', '-', '*', '/', '<', '>', '&', '|', '!', '%', '"', "'", '#'],
    ocaml: ['(', ')', '[', ']', '->', '|', '_', ';', ':', '=', '<', '>', '+', '-', '*', '"', "'", '::', 'let', 'in', 'match', 'with', 'fun'],
    python: ['(', ')', '[', ']', ':', '=', '_', ',', '+', '-', '*', '/', '%', '<', '>', '"', "'", 'def', 'return', 'if', 'else', 'for', 'in', 'None'],
    uir: ['%', '=', '#', '[', ']', '-', '.', 'add', 'mul', 'cmplt', 'where', 'param', 'dtype=i32', 'dtype=f32'],
  };
  function keybar(cm, lang, run, runLabel = 'Run') {
    const act = (label, f, wide) => h('button', { type: 'button', class: wide ? 'wide' : null, 'aria-label': label, text: label,
      onpointerdown: e => e.preventDefault(),            // keep focus in the editor so the keyboard stays up
      onclick: () => { f(); cm.focus(); } });
    const ins = t => act(t, () => cm.replaceSelection(/^[a-z]/.test(t) && t.length > 2 && !t.includes('=') ? t + ' ' : t), t.length > 2);
    return h('div', { class: 'ex-keys', role: 'toolbar', 'aria-label': 'Insert symbols' },
      act('Tab', () => cm.replaceSelection('  '), true), act('←', () => cm.execCommand('goCharLeft')), act('→', () => cm.execCommand('goCharRight')),
      ...KEYS[lang].map(ins), act('Undo', () => cm.undo(), true), act(runLabel, run, true));
  }

  function render(res, submit) {
    if (!res.ok) return [h('div', { class: 'verdict no', text: /error|invalid/i.test(res.error) ? 'Error' : 'Could not run' }), h('pre', {}, h('code', { text: res.error })),
      res.stdout ? h('pre', {}, h('code', { text: res.stdout })) : null].filter(Boolean);
    const all = res.passed === res.total;
    const v = h('div', { class: 'verdict ' + (all ? 'ok' : 'no'), text: all ? (submit ? `Accepted · ${res.total} / ${res.total} tests` : `Examples pass · ${res.total} / ${res.total}`) + (submit ? '' : '. Now submit.') : `Wrong answer · ${res.passed} / ${res.total} passed` });
    let n = 0, hn = 0;
    const chips = h('div', { class: 'cases' }, res.results.map(r => h('span', { class: 'case ' + (r.pass ? 'p' : 'f'), text: r.hidden ? `Hidden ${++hn}` : `Case ${++n}` })));
    const bad = res.results.find(r => !r.pass && r.input != null);
    const det = bad ? h('div', { class: 'detail' }, h('span', { text: 'input' }), h('span', { text: bad.input }), h('span', { text: 'expected' }), h('span', { text: bad.expect }),
      h('span', { text: 'got' }), h('span', { text: bad.got })) : null;
    return [v, chips, det, res.stdout ? h('div', {}, h('span', { class: 'label', text: 'Your output' }), h('pre', {}, h('code', { text: res.stdout }))) : null].filter(Boolean);
  }

  document.addEventListener('DOMContentLoaded', () => { frame(); quizzes(); exercises(); });
  return { h, graph, parseUir, stepper, code, NAV, quizzes, store };
})();
