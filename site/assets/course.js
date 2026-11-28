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
    { title: 'Start · Make it run', items: [
      ['start/01-run-a-program.html', 'Run your first program', 'S.1'], ['start/02-build-a-calculator.html', 'Build the thing that runs it', 'S.2']] },
    { title: 'Week 1 · UOps and rewrites', items: [
      ['week1/01-the-uop.html', 'The UOp', '1.1'], ['week1/02-uir-and-interpreting.html', '.uir and interpreting', '1.2'],
      ['week1/03-rewrites-and-folding.html', 'Rewrites and folding', '1.3'], ['week1/04-symbolic.html', 'Symbolic simplification', '1.4'],
      ['week1/05-call-and-param.html', 'CALL, PARAM, STACK, INDEX', '1.5'], ['week1/06-lab.html', 'Lab: your compiler', '1.6']] },
    { title: 'Week 2 · Floats, memory and rendering C', items: [
      ['week2/01-buffers-and-views.html', 'Floats, buffers and views', '2.1'], ['week2/02-load-store-after.html', 'Load, store, after', '2.2'],
      ['week2/03-bounds.html', 'Proving bounds', '2.3'], ['week2/04-rendering-c.html', 'Rendering C', '2.4'],
      ['week2/05-the-runtime.html', 'The runtime', '2.5'], ['week2/06-lab.html', 'Lab: memory and C', '2.6']] },
    { title: 'Week 3 · Loops', items: [
      ['week3/01-ranges.html', 'Ranges and ends', '3.1'], ['week3/02-memory-in-loops.html', 'Memory in loops', '3.2'],
      ['week3/03-gemm.html', 'A GEMM by hand', '3.3'], ['week3/04-conv.html', 'A convolution by hand', '3.4'],
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
    { title: 'Week 7 · Fast kernels', items: [
      ['week7/01-measuring.html', 'Measuring speed', '7.1'], ['week7/02-caches-and-tiling.html', 'Caches and tiling', '7.2'],
      ['week7/03-upcast.html', 'Upcast', '7.3'], ['week7/04-threads.html', 'Threads', '7.4'],
      ['week7/05-kernels.html', 'Kernels and outlining', '7.5'], ['week7/06-lab.html', 'Lab: fast kernels', '7.6']] },
    { title: 'Week 8 · GPUs', items: [
      ['week8/01-gpus.html', 'How a GPU runs code', '8.1'], ['week8/02-global-and-local.html', 'Global and local loops', '8.2'],
      ['week8/03-shared-memory.html', 'Shared memory and barriers', '8.3'], ['week8/04-rendering-cuda.html', 'Rendering CUDA', '8.4'],
      ['week8/05-getting-a-gpu.html', 'Getting a GPU', '8.5'], ['week8/06-lab.html', 'Lab: GPU kernels', '8.6']] },
    { title: 'Week 9 · GPUs, part 2', items: [
      ['week9/01-registers.html', 'Registers and register tiles', '9.1'], ['week9/02-fast-gemm.html', 'Fast GEMMs', '9.2'],
      ['week9/03-tensor-cores.html', 'Tensor cores', '9.3'], ['week9/04-convolutions.html', 'Convolutions', '9.4'],
      ['week9/05-flash-attention.html', 'Flash attention', '9.5'], ['week9/06-lab.html', 'Lab: fast GPU kernels', '9.6']] },
    { title: 'Week 10 · Multiple GPUs', items: [
      ['week10/01-more-than-one-gpu.html', 'More than one GPU', '10.1'], ['week10/02-device-loops.html', 'Device loops and shards', '10.2'],
      ['week10/03-moving-memory.html', 'Moving memory', '10.3'], ['week10/04-sharded-gemm.html', 'A GEMM on two GPUs', '10.4'],
      ['week10/05-training-on-many.html', 'Training on several GPUs', '10.5'], ['week10/06-lab.html', 'Lab: multiple GPUs', '10.6']] },
    { title: 'Learn Python', track: 'python', items: [
      ['learn/py-01-first-steps.html', 'First steps in Python', 'P.1'], ['learn/py-02-decisions-loops.html', 'Decisions, loops and functions', 'P.2'],
      ['learn/py-03-collections.html', 'Lists, dicts and sets', 'P.3'], ['learn/py-04-your-own-types.html', 'Your own types', 'P.4'],
      ['learn/py-05-recursion.html', 'Recursion and functions as values', 'P.5'], ['learn/py-06-files-errors-tests.html', 'Files, errors and testing', 'P.6']] },
    { title: 'Learn OCaml', track: 'ocaml', items: [
      ['learn/ml-01-first-steps.html', 'First steps in OCaml', 'O.1'], ['learn/ml-02-functions.html', 'Functions and types', 'O.2'],
      ['learn/ml-03-lists-matching.html', 'Lists and pattern matching', 'O.3'], ['learn/ml-04-your-own-types.html', 'Your own types', 'O.4'],
      ['learn/ml-05-mutation.html', 'Arrays, tables and mutation', 'O.5'], ['learn/ml-06-modules-projects.html', 'Modules, maps and projects', 'O.6']] },
    { title: 'Week 0 · Prerequisites', items: [
      ['week0/01-c-and-pointers.html', 'C and pointers', '0.1'], ['week0/02-memory-and-caches.html', 'Memory and caches', '0.2'],
      ['week0/03-compilers-and-irs.html', 'Compilers and IRs', '0.3'], ['week0/04-tensors-and-shapes.html', 'Tensors and shapes', '0.4'],
      ['week0/05-matmul.html', 'Matrix multiply', '0.5'], ['week0/06-ocaml.html', 'OCaml crash course', '0.6'],
      ['week0/07-python.html', 'Python for this course', '0.7']] },
    { title: 'Hard ideas, slowly', items: [
      ['learn/hard-01-sharing.html', 'Sharing nodes', 'H.1'], ['learn/hard-02-walking-graphs.html', 'Walking a graph once', 'H.2'],
      ['learn/hard-03-rewriting.html', 'Rewriting until nothing changes', 'H.3'], ['learn/hard-04-numbers-like-c.html', 'Numbers that behave like C', 'H.4']] },
    { title: 'Resources', items: [['resources/index.html', 'All resources'], ['resources/bug-hunts.html', 'Bug hunts'], ['resources/debugging.html', 'Debugging your compiler'],
      ['resources/review.html', 'Quiz review'], ['resources/glossary.html', 'Glossary'], ['resources/languages.html', 'Python and OCaml, deeper']] }
  ];
  const ROOT = () => document.body.dataset.root || './';
  // The course's source, linked from the top bar of every page
  const REPO = 'https://github.com/wilsonmike/ml-compilers-course';
  // Google Analytics 4, through the Google tag container (it carries the GA4 stream, G-5W4EDH8RFN). Only on the
  // live site, so local copies and previews never count as visits.
  const TAG_ID = 'GTM-MPMCLH74';
  if (/(^|\.)sharpterminal\.com$/.test(location.hostname)) {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });
    const s = document.createElement('script'); s.async = true; s.src = 'https://www.googletagmanager.com/gtm.js?id=' + TAG_ID;
    document.head.append(s);
  }
  if (location.protocol !== 'file:' && window.HTMLScriptElement && HTMLScriptElement.supports && HTMLScriptElement.supports('speculationrules')) {
    const sr = document.createElement('script'); sr.type = 'speculationrules';
    sr.textContent = JSON.stringify({ prefetch: [{ where: { and: [{ href_matches: '/*' }, { not: { href_matches: '/api/*' } }] }, eagerness: 'moderate' }] });
    document.head.append(sr);
  }
  const ghLink =() => { const a = h('a', { class: 'gh', href: REPO, title: 'The course on GitHub', 'aria-label': 'The course on GitHub' });
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
  function segPick(label, options, current, pick) {
    const g = h('div', { class: 'seg', role: 'group', 'aria-label': label });
    g.paint = v => g.querySelectorAll('button').forEach(b => { const on = b.dataset.v === v; b.classList.toggle('on', on); b.setAttribute('aria-pressed', String(on)); });
    options.forEach(([v, t]) => g.append(h('button', { type: 'button', 'data-v': v, text: t, onclick: () => pick(v) })));
    g.paint(current); return g;
  }
  function setTrack(v) {
    if (v === track()) return;
    store.set('cc-track', v);
    if (!document.getElementById('you')) { location.reload(); return; }
    document.documentElement.dataset.track = v;
    document.querySelectorAll('.seg[data-pick="track"]').forEach(g => g.paint(v));
    document.dispatchEvent(new Event('cc-progress'));
  }
  function trackSelect() {
    const g = segPick('Language you write your compiler in', TRACKS, track(), setTrack);
    g.dataset.pick = 'track'; return g;
  }
  const TOUCH = matchMedia('(any-pointer: coarse)').matches || /[?&]touch=1/.test(location.search);
  if (TOUCH) document.documentElement.classList.add('touch');

  const today = (d = new Date()) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  const addDays = (n, d = new Date()) => { const x = new Date(d); x.setDate(x.getDate() + n); return today(x); };
  const readJSON = (k, d) => { try { const v = JSON.parse(store.get(k)); return v == null ? d : v; } catch { return d; } };
  const keysWith = prefix => { const out = []; try { for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (k && k.startsWith(prefix)) out.push(k); } } catch {} return out; };
  const changed = () => document.dispatchEvent(new Event('cc-progress'));
  function studied() { const ds = readJSON('cc-days', []), t = today(); if (ds[ds.length - 1] !== t) { ds.push(t); store.set('cc-days', JSON.stringify(ds.slice(-400))); } }
  const isDone = href => !!store.get('cc-done:' + href);
  const prog = href => { try { return JSON.parse(store.get('cc-prog:' + href) || 'null'); } catch { return null; } };
  const lessonDone = href => { const p = prog(href); return isDone(href) || !!(p && p.t && p.s >= p.t); };
  function setDone(href, on) { if (on) { if (!isDone(href)) store.set('cc-done:' + href, today()); studied(); } else { try { localStorage.removeItem('cc-done:' + href); } catch {} } changed(); }
  const GAPS = [1, 3, 7, 16, 35, 90];
  function schedule(qid, ok) {
    const r = readJSON('cc-q:' + qid, null);
    studied();
    if (ok && r && r.due > today()) return;
    const b = ok ? Math.min((r ? r.b : 0) + 1, GAPS.length - 1) : 0;
    store.set('cc-q:' + qid, JSON.stringify({ b, due: addDays(GAPS[b]) }));
  }
  const REVIEW_MAX = 10;
  const offTrackHref = href => (track() === 'python' ? href.startsWith('learn/ml-') || href === 'week0/06-ocaml.html' : href.startsWith('learn/py-') || href === 'week0/07-python.html');
  const dueQuizzes = () => keysWith('cc-q:').map(k => [k.slice(5), readJSON(k, {}).due || '9']).filter(([q, d]) => d <= today() && !offTrackHref(q.split('#')[0])).sort((a, b) => (a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0)).map(([q]) => q);
  const nextReview = () => keysWith('cc-q:').filter(k => !offTrackHref(k.slice(5).split('#')[0])).map(k => readJSON(k, {}).due).filter(d => d && d > today()).sort()[0] || null;
  const forget = qid => { try { localStorage.removeItem('cc-q:' + qid); } catch {} };

  const LANG_LESSON = { 'week0/06-ocaml.html': 'ocaml', 'week0/07-python.html': 'python' };
  const langLesson = () => (track() === 'python' ? 'week0/07-python.html' : 'week0/06-ocaml.html');
  const onTrack = ([href]) => !LANG_LESSON[href] || href === langLesson();
  const onTrackItem = item => onTrack(item) && !offTrackHref(item[0]);
  const weeksFrom = n => NAV.filter(g => { const m = /^Week (\d+)/.exec(g.title); return m && +m[1] >= n; });
  const hardIdeas = () => NAV.find(g => g.title.startsWith('Hard ideas'));
  const langName = () => (track() === 'python' ? 'Python' : 'OCaml');
  const startGroup = () => NAV.find(g => g.title.startsWith('Start ·'));
  const startStep = n => ({ title: startGroup().title, items: [startGroup().items[n]] });
  const shelf = (...hrefs) => ({ title: 'Week 0 · Prerequisites', items: hrefs.map(x => NAV.flatMap(g => g.items).find(([href]) => href === x)) });
  const week = n => NAV.find(g => g.title.startsWith(`Week ${n} `));
  const spine = () => [shelf(langLesson()), week(1), shelf('week0/01-c-and-pointers.html'), week(2), shelf('week0/04-tensors-and-shapes.html', 'week0/05-matmul.html'),
    week(3), week(4), week(5), week(6), shelf('week0/02-memory-and-caches.html'), ...weeksFrom(7)];
  const PATHS = {
    new: { name: 'I’m new to programming', short: 'new to programming', about: () => `Run a program first, learn ${langName()} from scratch, then build the compiler one step at a time.`,
      groups: () => [startStep(0), NAV.find(g => g.track === track()), startStep(1), ...spine()] },
    coder: { name: 'I can already program', short: 'can already program', about: () => 'Run a program, write a tiny interpreter, then build the compiler. C and matrix math arrive just before the week that needs them.',
      groups: () => [startGroup(), ...spine()] },
    expert: { name: 'I know C and compilers', short: 'know C and compilers', about: () => `Set up ${langName()} in lesson ${track() === 'python' ? '0.7' : '0.6'}, then go straight to week 1.`,
      groups: () => [shelf(langLesson()), ...weeksFrom(1)] },
  };
  const pathId = () => (PATHS[store.get('cc-path')] ? store.get('cc-path') : null);
  const pathItems = id => PATHS[id].groups().flatMap(g => g.items.filter(onTrack).map(i => [...i, g.title]));
  const nextUp = (id, after) => { const items = pathItems(id), i = after ? items.findIndex(x => x[0] === after) : -1;
    return items.slice(i + 1).find(x => !lessonDone(x[0])) || (after ? null : items.find(x => !lessonDone(x[0]))) || null; };

  // ---- runner (tools/serve.py) ----
  let runnerP = null;
  const localHost = /^(127\.0\.0\.1|localhost|\[::1\])$/.test(location.hostname);
  const runner = () => runnerP ||= (location.protocol.startsWith('http') && localHost
    ? fetch(ROOT() + '../api/health', { cache: 'no-store' }).then(r => r.ok ? r.json() : null).catch(() => null) : Promise.resolve(null));
  const api = p => ROOT() + '../api/' + p;

  // ---- shell ----
  function frame() {
    const b = document.body, root = ROOT(), cur = here(), main = document.querySelector('main');
    const offTrack = href => (cur && cur[1][0] === href ? null : LANG_LESSON[href] ? 'only-' + LANG_LESSON[href] : null);
    const item = ([href, title, n]) => h('li', { class: offTrack(href) }, h('a', { href: root + href, 'data-href': n ? href : null, class: cur && cur[1][0] === href ? 'on' : null, 'aria-current': cur && cur[1][0] === href ? 'page' : null },
      n ? h('span', { class: 'n', text: n }) : null, h('span', { text: title }), n ? h('span', { class: 'prog' }) : null));
    const top = h('ul', { class: 'top' });
    const nav = h('nav', { 'aria-label': 'Lessons' }, NAV.map(g => {
      if (g.title === 'Start here') { top.append(...g.items.map(item)); return top; }
      const gk = 'cc-grp:' + g.title, closed = store.get(gk) === '0';
      const grp = h('div', { class: 'grp' + (closed ? ' closed' : '') + (g.track && !(cur && cur[0] === g) ? ' only-' + g.track : ''), 'data-gk': gk });
      grp.append(h('button', { type: 'button', 'aria-expanded': String(!closed), onclick: () => {
        const c = grp.classList.toggle('closed'); grp.firstChild.setAttribute('aria-expanded', String(!c)); store.set(gk, c ? '0' : '1'); } },
        h('span', { class: 'chev', 'aria-hidden': 'true' }, h('svg', { width: 10, height: 10, viewBox: '0 0 10 10' }, h('path', { d: 'M2 3.5l3 3 3-3', stroke: 'currentColor', 'stroke-width': 1.5, fill: 'none' }))),
        h('span', { text: g.title }), h('span', { class: 'gcount' })));
      grp.append(h('ul', {}, g.items.map(item)));
      return grp; }));
    const paintSide = () => {
      nav.querySelectorAll('a[data-href]').forEach(a => { const href = a.dataset.href, p = prog(href), m = a.querySelector('.prog');
        const all = p && p.t && p.s >= p.t, d = isDone(href) || all;
        m.className = 'prog' + (d ? ' done' : ''); m.textContent = d ? '✓' : p && p.s > 0 ? `${p.s}/${p.t}` : '';
        m.title = d ? 'Done' : p && p.s > 0 ? `${p.s} of ${p.t} exercises solved` : ''; });
      nav.querySelectorAll('.grp').forEach(g => { const ls = [...g.querySelectorAll('a[data-href]')].filter(a => onTrack([a.dataset.href]));
        const k = ls.filter(a => a.querySelector('.prog.done')).length, c = g.querySelector('.gcount');
        c.textContent = k ? `${k}/${ls.length}` : ''; c.title = k ? `${k} of ${ls.length} lessons done` : ''; });
      top.querySelectorAll('.extra').forEach(x => x.remove());
      const pid = pathId(), nx = pid && nextUp(pid), due = dueQuizzes().length;
      if (nx && !(cur && cur[1][0] === nx[0])) top.append(h('li', { class: 'extra' }, h('a', { href: root + nx[0], title: 'The next lesson on your path' }, h('span', { class: 'n', text: '→' }), h('span', { text: `Next: ${nx[2]} ${nx[1]}` }))));
      if (due) top.append(h('li', { class: 'extra' }, h('a', { href: root + 'resources/review.html?mode=due', title: 'Quiz questions due for review' }, h('span', { class: 'n', text: '↺' }), h('span', { text: 'Review' }), h('span', { class: 'prog', text: String(due) })))); };
    paintSide();
    document.addEventListener('cc-progress', paintSide);
    const search = h('input', { type: 'search', placeholder: 'Search lessons', 'aria-label': 'Search lessons', oninput: () => {
      const q = search.value.trim().toLowerCase();
      nav.querySelectorAll('li').forEach(li => (li.hidden = !!(q && !li.textContent.toLowerCase().includes(q))));
      nav.querySelectorAll('.grp').forEach(g => {
        if (q) { const any = [...g.querySelectorAll('li')].some(li => !li.hidden); g.hidden = !any; g.classList.remove('closed'); }
        else { g.hidden = false; g.classList.toggle('closed', store.get(g.dataset.gk) === '0'); }
      }); } });
    const seg = h('div', { class: 'seg', role: 'group', 'aria-label': 'Theme' });
    const paintSeg = () => seg.querySelectorAll('button').forEach(x => { const on = x.dataset.t === theme(); x.classList.toggle('on', on); x.setAttribute('aria-pressed', String(on)); });
    ['light', 'dark'].forEach(t => seg.append(h('button', { type: 'button', 'data-t': t, text: t[0].toUpperCase() + t.slice(1), onclick: () => {
      document.documentElement.dataset.theme = t; store.set('cc-theme', t); paintSeg(); } })));
    paintSeg();
    const km = keymapSelect();
    const side = h('aside', { class: 'side' },
      h('a', { class: 'brand', href: root + 'index.html' }, h('span', { class: 'mark', 'aria-hidden': 'true' }), 'ML compilers, from zero'),
      h('div', { class: 'search' }, search),
      h('div', { class: 'foot' }, h('div', { class: 'row' }, 'Language', trackSelect()), h('div', { class: 'row' }, 'Theme', seg), h('div', { class: 'row' }, 'Keys', km)), nav);
    const pill = h('span', { class: 'runner', title: 'Start it with: python tools/serve.py' }, h('span', { class: 'dot' }), 'Runner off');
    runner().then(r => {
      if (r) { pill.classList.add('on'); pill.lastChild.textContent = 'Runner on'; pill.title = 'Exercises run on your machine via tools/serve.py'; }
      else if (location.protocol.startsWith('http') && typeof Worker !== 'undefined') {
        pill.classList.add('on'); pill.lastChild.textContent = 'Browser runner';
        pill.title = 'Python and .uir exercises run in your browser (WebAssembly). For C and OCaml, run: python tools/serve.py';
      }
    });
    const isHome = b.classList.contains('home');
    const subPage = !cur && /\/resources\/(week\d+|tests-week\d+)(\.html)?$/.test(location.pathname.replace(/\\/g, '/'));
    const crumbs = h('div', { class: 'crumbs' }, isHome ? [h('span', { text: 'sharpterminal.com' })]
      : cur ? [h('a', { href: root + 'index.html', text: 'Course' }),
      ...(cur[0].title === 'Start here' ? [] : [h('span', { class: 'sep', text: '/' }), cur[0].title.split(' · ')[0]]),
      h('span', { class: 'sep', text: '/' }), cur[1][1]]
      : subPage ? [h('a', { href: root + 'index.html', text: 'Course' }), h('span', { class: 'sep', text: '/' }),
        h('a', { href: root + 'resources/index.html', text: 'Resources' }), h('span', { class: 'sep', text: '/' }),
        (main && main.querySelector('h1') ? main.querySelector('h1').textContent : document.title)] : []);
    const app = h('div', { class: 'app' });
    const menu = h('button', { class: 'menu', type: 'button', 'aria-label': 'Open lessons', 'aria-expanded': 'false' },
      h('svg', { width: 20, height: 20, viewBox: '0 0 20 20', 'aria-hidden': 'true' }, h('path', { d: 'M3 6h14M3 10h14M3 14h14', stroke: 'currentColor', 'stroke-width': 1.6, fill: 'none' })));
    const scrim = h('div', { class: 'scrim' });
    const page = h('div', { class: 'page' }, h('div', { class: 'docwrap' }, main || ''));
    const wrap = h('div', { class: 'mainwrap' }, h('header', { class: 'topbar' }, menu, crumbs, pill, ghLink()), page);
    app.append(side, scrim, wrap);
    b.prepend(app);
    if (main) { if (!main.id) main.id = 'main'; main.tabIndex = -1; b.prepend(h('a', { class: 'skip', href: '#' + main.id, text: 'Skip to content' })); }
    const onLink = side.querySelector('nav a.on');
    if (onLink && side.scrollHeight > side.clientHeight) side.scrollTop = onLink.getBoundingClientRect().top - side.getBoundingClientRect().top - side.clientHeight / 3;
    const you = document.getElementById('you'); if (you) { homePanel(you); document.addEventListener('cc-progress', () => homePanel(you)); }
    if (main && !isHome) toc(main, page);
    document.querySelectorAll('[data-prog]').forEach(a => { const p = prog(a.dataset.prog), d = isDone(a.dataset.prog) || (p && p.t && p.s >= p.t);
      a.append(h('span', { class: 'p' + (d ? ' done' : ''), text: d ? 'Done' : p && p.s ? `${p.s}/${p.t}` : '' })); });
    if (main && cur && cur[1][2]) lessonTools(main, cur);
    if (main && cur && cur[1][2]) stepMode(main, cur);
    // the drawer is modal on small screens: lock the page behind it, close on Escape or on navigation
    const setOpen = open => { app.classList.toggle('open', open); wrap.inert = open; menu.setAttribute('aria-expanded', String(open)); if (open) (side.querySelector('nav a.on') || side.querySelector('nav a'))?.focus(); };
    const desk = matchMedia('(min-width: 901px)');
    const paintMenu = () => { const off = app.classList.contains('side-off'), l = desk.matches ? (off ? 'Show lessons' : 'Hide lessons') : 'Open lessons';
      menu.setAttribute('aria-label', l); menu.title = desk.matches ? `${l} (${/Mac/.test(navigator.platform) ? '⌘' : 'Ctrl'}+\\)` : l;
      if (desk.matches) menu.setAttribute('aria-expanded', String(!off)); };
    const toggleSide = () => { const off = app.classList.toggle('side-off'); store.set('cc-side', off ? '0' : '1'); paintMenu(); };
    if (store.get('cc-side') === '0') app.classList.add('side-off');
    paintMenu(); desk.addEventListener('change', paintMenu);
    menu.onclick = () => (desk.matches ? toggleSide() : setOpen(true)); scrim.onclick = () => setOpen(false);
    side.addEventListener('click', e => { if (e.target.closest('a') && app.classList.contains('open')) setOpen(false); });
    addEventListener('keydown', e => { if (e.key === '\\' && (e.ctrlKey || e.metaKey) && desk.matches) { e.preventDefault(); toggleSide(); } });
    addEventListener('keydown', e => { if (e.key === 'Escape' && app.classList.contains('open')) { setOpen(false); menu.focus(); } });
    matchMedia('(min-width: 901px)').addEventListener('change', e => e.matches && setOpen(false));
  }

  const onPage = q => !q.closest(track() === 'python' ? '.only-ocaml' : '.only-python');
  const plural = (n, w) => `${n} ${w}${n === 1 ? '' : w.endsWith('z') ? 'zes' : 's'}`;

  function pagerFor(pager, href) {
    const root = ROOT(), pid = pathId(), every = NAV.flatMap(g => g.items.filter(i => i[2]).map(i => [...i, g.title]));
    const lang = NAV.find(g => g.track && g.items.some(i => i[0] === href)), tag = (g, xs) => xs.map(i => [...i, g.title]);
    const langSeq = lang && [...tag(startGroup(), startStep(0).items), ...tag(lang, lang.items), ...tag(startGroup(), startStep(1).items)];
    const seq = [pid && pathItems(pid), pathItems('new'), langSeq, every].find(s => s && s.some(x => x[0] === href));
    const i = seq.findIndex(x => x[0] === href), prev = seq[i - 1], next = seq[i + 1];
    pager.replaceChildren(
      h('a', { href: root + (prev ? prev[0] : 'index.html'), text: prev ? `← ${prev[2]} ${prev[1]}` : '← Course home' }),
      h('a', { href: root + (next ? next[0] : 'index.html'), text: next ? `${next[2]} ${next[1]} →` : 'Course home →' }));
  }

  function lessonTools(main, cur) {
    const href = cur[1][0], root = ROOT();
    const pg = main.querySelector('nav.pager'); if (pg) pagerFor(pg, href);
    const core = main.cloneNode(true); core.querySelectorAll('details').forEach(d => d.remove());
    const words = (core.textContent || '').split(/\s+/).filter(Boolean).length;
    const nq = [...main.querySelectorAll('.quiz')].filter(onPage).length, nx = main.querySelectorAll('.exercise[data-ex]').length;
    const figs = core.querySelectorAll('.fig, figure, table').length, lab = /^Lab:/.test(cur[1][1]);
    const mins = Math.max(10, Math.round((words / 160 + figs + nq * 0.5 + nx * 4) / 5) * 5);
    const state = h('span', { class: 'state' });
    const meta = h('p', { class: 'lesson-meta' }, h('span', { text: lab ? `About ${mins} min to read, then the build` : `About ${mins} min` }), nq ? h('span', { text: plural(nq, 'quiz') }) : null, nx ? h('span', { text: plural(nx, 'exercise') }) : null, state);
    (main.querySelector('.lede') || main.querySelector('h1')).after(meta);
    // Spaced-retrieval warm-up: surface due review questions right before new material
    const due = dueQuizzes().length;
    let dismissed = false; try { dismissed = sessionStorage.getItem('cc-warmup-off') === '1'; } catch {}
    if (due && !dismissed) {
      const n = Math.min(due, REVIEW_MAX);
      const bar = h('div', { class: 'warmup' },
        h('span', { class: 'w-ic', 'aria-hidden': 'true', text: '↺' }),
        h('span', { class: 'w-txt', text: `Warm-up: ${plural(due, 'review question')} due from earlier lessons.` }),
        h('a', { class: 'btn', href: root + 'resources/review.html?mode=due', text: `Review ${n} now →` }),
        h('button', { type: 'button', class: 'linkish w-x', 'aria-label': 'Dismiss warm-up', text: 'Later', onclick: () => { try { sessionStorage.setItem('cc-warmup-off', '1'); } catch {} bar.remove(); } }));
      meta.after(bar);
    }
    const pager = main.querySelector('nav.pager');
    const fin = h('div', { class: 'finish' });
    const paint = () => {
      const d = isDone(href), pid = pathId(), nx1 = pid && nextUp(pid, href), pn = pager && pager.querySelector('a:last-child:not(:first-child)');
      const nxt = nx1 && !(pn && new URL(pn.href, location.href).pathname.replace(/\.html$/, '') === new URL(root + nx1[0], location.href).pathname.replace(/\.html$/, '')) ? nx1 : null;
      state.textContent = d ? '✓ Done' : ''; state.hidden = !d;
      fin.replaceChildren(...(d
        ? [h('span', { class: 'ok', text: '✓ Lesson done' }), nxt ? h('a', { href: root + nxt[0], text: `Next on your path: ${nxt[2]} ${nxt[1]} →` }) : null,
           h('button', { type: 'button', class: 'linkish', text: 'Undo', onclick: () => setDone(href, false) })]
        : [h('button', { type: 'button', class: 'btn', text: 'Mark lesson as done', onclick: () => setDone(href, true) }),
           nq ? h('span', { class: 'muted', text: 'It also counts as done once you’ve answered every quiz.' }) : null]).filter(Boolean));
    };
    if (pager) pager.before(fin); else main.append(fin);
    paint(); document.addEventListener('cc-progress', paint);
  }

  const TRACK_CARDS = {
    python: { logo: 'assets/logo-python.svg', about: 'The quickest start. Spend your time on the compiler, not on a new language.' },
    ocaml: { logo: 'assets/logo-ocaml.svg', about: 'Pattern matching and a type checker that catch compiler bugs early.' } };
  function trackCards() {
    const root = ROOT(), cur = track();
    return h('div', { class: 'tracks', role: 'group', 'aria-label': 'Language you write your compiler in' }, TRACKS.map(([v, name]) => {
      const on = v === cur;
      return h('button', { type: 'button', class: 'track' + (on ? ' on' : ''), 'aria-pressed': String(on), 'data-key': 'track-' + v, onclick: () => setTrack(v) },
        h('img', { class: 'logo', src: root + TRACK_CARDS[v].logo, alt: '', width: 40, height: 40 }),
        h('span', { class: 'tt' }, h('span', { class: 't', text: name }), h('span', { class: 'd', text: TRACK_CARDS[v].about })),
        h('span', { class: 'pick', text: on ? '✓ Selected' : `Choose ${name}` })); }));
  }

  function homePanel(el) {
    const root = ROOT(), pid = pathId(), act = document.activeElement, back = act && el.contains(act) ? act.dataset.key : null;
    const heading = t => { const x = h('h2', { id: 'progress', text: t }); const a = document.querySelector('.toc a[href="#progress"]'); if (a) a.textContent = t; return x; };
    const refocus = (...keys) => { const k = keys.find(k => el.querySelector(`[data-key="${k}"]`)); if (k) el.querySelector(`[data-key="${k}"]`).focus(); };
    const lang = (title) => [h('h3', { class: 'step', text: title }), trackCards(),
      h('p', { class: 'muted tracks-note', text: 'Both tracks teach the language from scratch, share every other lesson and pass the same tests. You can switch later.' })];
    if (!pid) {
      el.replaceChildren(heading('Start here'),
        ...lang('1. Pick the language you’ll write your compiler in'),
        h('h3', { class: 'step', text: '2. Pick where you’re starting from' }),
        h('ul', { class: 'paths' }, Object.entries(PATHS).map(([k, p]) => { const items = pathItems(k);
          return h('li', {}, h('button', { type: 'button', 'data-key': 'path-' + k, onclick: () => { store.set('cc-path', k); changed(); } },
            h('span', { class: 't', text: p.name }), h('span', { class: 'd', text: p.about() }),
            h('span', { class: 'c', text: `${items.length} lessons. You start with ${items[0][2]} ${items[0][1]}.` }))); })));
      if (back) refocus(back, 'path-new');
      return;
    }
    const items = pathItems(pid), done = items.filter(x => lessonDone(x[0])).length, nx = nextUp(pid);
    const days = new Set(readJSON('cc-days', [])), now = new Date(), dow = (now.getDay() + 6) % 7, t = today();
    const week = [...Array(7)].map((_, i) => addDays(i - dow));
    const thisWeek = week.filter(d => days.has(d)).length, lastWeek = [...Array(7)].map((_, i) => addDays(i - dow - 7)).filter(d => days.has(d)).length;
    const due = dueQuizzes().length, fresh = !done && !days.size && !due && !keysWith('cc-q:').length;
    el.replaceChildren(...[heading('Your progress'),
      h('div', { class: 'you' + (fresh ? ' fresh' : '') },
        nx ? h('a', { class: 'you-next', href: root + nx[0], 'data-key': 'next' }, h('span', { class: 'label', text: 'Next up' }), h('span', { class: 't', text: `${nx[2]} ${nx[1]}` }), h('span', { class: 'd', text: nx[3] }))
           : h('div', { class: 'you-next' }, h('span', { class: 'label', text: 'Path finished' }), h('span', { class: 't', text: 'You’ve done every lesson on this path.' })),
        h('div', { class: 'you-cell' }, h('span', { class: 'label', text: 'Your path' }),
          h('span', { class: 'v', text: `${done} of ${items.length} lessons` }),
          h('span', { class: 'bar', role: 'progressbar', 'aria-valuemin': '0', 'aria-valuemax': String(items.length), 'aria-valuenow': String(done), 'aria-label': 'Lessons done on your path' },
            h('span', { style: `width:${(100 * done / items.length).toFixed(1)}%` }))),
        h('div', { class: 'you-cell' }, h('span', { class: 'label', text: 'This week' }),
          h('span', { class: 'days', role: 'img', 'aria-label': `Studied ${plural(thisWeek, 'day')} this week` }, week.map((d, i) =>
            h('span', { class: 'day' + (days.has(d) ? ' on' : '') + (d === t ? ' now' : '') + (d > t ? ' later' : ''), title: d, text: 'MTWTFSS'[i] }))),
          h('span', { class: 'd', text: (thisWeek ? `${plural(thisWeek, 'day')} so far` : 'Nothing yet this week') + (lastWeek ? `, ${lastWeek} last week` : '') })),
        h('div', { class: 'you-cell you-rev' }, h('span', { class: 'label', text: 'Review' }),
          due ? h('span', { class: 'v', text: `${plural(due, 'question')} due` }) : h('span', { class: 'v', text: 'Nothing due' }),
          due ? h('a', { class: 'btn primary', href: root + 'resources/review.html?mode=due', text: due > REVIEW_MAX ? `Review ${REVIEW_MAX} now, about ${REVIEW_MAX / 2} min` : `Review now, about ${Math.max(1, Math.ceil(due / 2))} min` })
              : h('span', { class: 'd', text: 'Quiz questions come back after 3 days if you got them right, the next day if not, and then at longer gaps.' }))),
      h('p', { class: 'muted you-foot' }, `Your path: ${PATHS[pid].short}. `,
        h('button', { type: 'button', class: 'linkish', 'data-key': 'change', text: 'Change path', onclick: () => { try { localStorage.removeItem('cc-path'); } catch {} changed(); } }),
        ' · Progress is saved in this browser only.'),
      ...lang('Your language')].filter(Boolean));
    if (back) refocus(back, 'next');
  }

  // "On this page": every h2, with the one you're reading highlighted
  function stepMode(main, cur) {
    const href = cur[1][0], label = `${cur[1][2]} ${cur[1][1]}`;
    [...main.querySelectorAll(':scope > .prose')].forEach(p => {
      const kids = [...p.children];
      if (!kids.some((k, i) => i && k.tagName === 'H2')) return;
      let at = p;
      kids.forEach((k, i) => { if (i && k.tagName === 'H2') { const d = h('div', { class: p.className }); at.after(d); at = d; } if (at !== p) at.append(k); });
    });
    const starts = k => k.tagName === 'H2' || (k.classList.contains('prose') && k.firstElementChild && k.firstElementChild.tagName === 'H2');
    const tail = k => k.matches('nav.pager, .finish');
    const groups = [[]]; let seen = false;
    [...main.children].filter(k => !tail(k)).forEach(k => { if (starts(k)) { if (seen) groups.push([]); seen = true; } groups[groups.length - 1].push(k); });
    if (groups.length < 3) return;
    const secs = groups.map(g => { const sec = h('section', { class: 'step', tabindex: '-1' }); g[0].before(sec); sec.append(...g); return sec; });
    const titles = secs.map(sec => (sec.querySelector('h2') || {}).textContent || 'Start');
    const ends = [...main.children].filter(tail);
    const fill = h('span'), where = h('span', { class: 'sb-where' }), mode = h('button', { type: 'button', class: 'linkish' });
    const bar = h('div', { class: 'stepbar' }, where, h('span', { class: 'sb-track', role: 'progressbar', 'aria-valuemin': '1', 'aria-valuemax': String(secs.length), 'aria-label': 'Parts of this lesson' }, fill), mode);
    const back = h('button', { type: 'button', class: 'btn', text: '← Back' }), next = h('button', { type: 'button', class: 'btn primary lg' });
    const nav = h('div', { class: 'stepnav' }, back, next);
    main.prepend(bar); secs[secs.length - 1].after(nav);
    let i = 0, all = store.get('cc-steps') === 'all';
    const paint = () => {
      secs.forEach((sec, j) => { sec.hidden = !all && j !== i; });
      ends.forEach(e => { e.hidden = !all && i !== secs.length - 1; });
      nav.hidden = all; back.disabled = i === 0; next.hidden = i === secs.length - 1;
      next.textContent = i < secs.length - 1 ? `Next: ${titles[i + 1]} →` : '';
      where.textContent = all ? `${label} · ${secs.length} parts on one page` : `${label} · Part ${i + 1} of ${secs.length}`;
      fill.style.width = `${all ? 100 : (100 * (i + 1) / secs.length).toFixed(1)}%`;
      bar.querySelector('.sb-track').setAttribute('aria-valuenow', String(i + 1));
      mode.textContent = all ? 'Show one part at a time' : 'Show the whole lesson';
      (all ? main : secs[i]).querySelectorAll('.CodeMirror').forEach(c => c.CodeMirror && c.CodeMirror.refresh());
      document.dispatchEvent(new Event('cc-step'));
    };
    const go = (j, scroll) => { i = Math.max(0, Math.min(secs.length - 1, j)); store.set('cc-step:' + href, String(i)); paint(); if (scroll) bar.scrollIntoView({ block: 'start' }); };
    const fromHash = () => {
      const el = location.hash.length > 1 && document.getElementById(decodeURIComponent(location.hash.slice(1)));
      const sec = el && el.closest('section.step');
      if (!sec) return false;
      go(secs.indexOf(sec)); el.scrollIntoView({ block: 'start' }); return true;
    };
    const turn = (e, d) => { go(i + d, true); if (!e.detail) secs[i].focus({ preventScroll: true }); };
    back.onclick = e => turn(e, -1); next.onclick = e => turn(e, 1);
    mode.onclick = () => { all = !all; store.set('cc-steps', all ? 'all' : 'one'); paint(); bar.scrollIntoView({ block: 'start' }); };
    addEventListener('hashchange', fromHash);
    if (!fromHash()) go(isDone(href) ? 0 : +store.get('cc-step:' + href) || 0);
  }
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
    const pick = () => { const vis = hs.filter(x => x.offsetParent), top = vis.find(x => seen.get(x.id)); if (top) mark(top.id);
      else { const above = vis.filter(x => x.getBoundingClientRect().top < 120).pop(); mark((above || vis[0] || hs[0]).id); } };
    const io = new IntersectionObserver(es => { es.forEach(e => seen.set(e.target.id, e.isIntersecting)); pick(); }, { rootMargin: '-60px 0px -55% 0px' });
    hs.forEach(x => io.observe(x));
    document.addEventListener('cc-step', pick);
  }

  // ---- DAG drawing. nodes: [{id, op, sub, src:[id], cls, val, ecls}] ; sources on top, results flow down ----
  function graph(nodes, { width } = {}) {
    const by = new Map(nodes.map(n => [n.id, n])), depth = new Map();
    const d = n => { if (depth.has(n.id)) return depth.get(n.id); depth.set(n.id, 0);
      const v = (n.src || []).length ? 1 + Math.max(...n.src.map(s => d(by.get(s)))) : 0; depth.set(n.id, v); return v; };
    nodes.forEach(d);
    const route = new Map(), lay = [...nodes];
    nodes.forEach(n => (n.src || []).forEach((s, i) => { const ids = []; let prev = s;
      for (let k = depth.get(s) + 1; k < depth.get(n.id); k++) { const id = `${n.id}~${i}~${k}`; lay.push({ id, dummy: true, op: '', src: [prev] }); depth.set(id, k); ids.push(id); prev = id; }
      if (ids.length) route.set(n.id + '~' + i, ids); }));
    const rows = []; lay.forEach(n => (rows[depth.get(n.id)] ||= []).push(n));
    const NW = n => (n.dummy ? 10 : Math.max(56, 9 * Math.max(n.op.length, (n.sub || '').length) + 24)), NH = n => n.sub ? 50 : 34, GAP = 20, RH = 84;
    const VW = n => (n.val != null ? 6 + 9 * ('= ' + n.val).length : 0);
    const x = new Map();
    const place = row => { let cx = 0; row.forEach(n => { x.set(n.id, cx + NW(n) / 2); cx += NW(n) + VW(n) + GAP; }); return cx - GAP; };
    rows.forEach(place);
    const via = (n, i) => { const r = route.get(n.id + '~' + i); return r ? r[r.length - 1] : n.src[i]; };
    const bary = n => { const s = (n.src || []).map((_, i) => x.get(via(n, i))); return s.length ? s.reduce((a, b) => a + b) / s.length : 0; };
    for (let pass = 0; pass < 4; pass++) rows.forEach((row, i) => { if (i) { row.sort((a, b) => bary(a) - bary(b)); place(row); } });
    const W = Math.max(...rows.map(r => place(r)));
    rows.forEach(r => { const w = place(r), off = (W - w) / 2; r.forEach(n => x.set(n.id, x.get(n.id) + off)); });
    const y = n => 12 + depth.get(n.id) * RH;
    const z = parseFloat(getComputedStyle(document.documentElement).fontSize) / 16 || 1;
    const svg = h('svg', { class: 'g', viewBox: `-8 0 ${W + 16} ${rows.length * RH}`, width: Math.round((width || W + 16) * z), role: 'img',
      'aria-label': 'Graph with ' + plural(nodes.length, 'box') + ': ' + nodes.map(n => n.op).join(', ') });
    const edges = h('g'), ns = h('g');
    const mid = 'gm' + (graph.count = (graph.count || 0) + 1);
    const tip = (id, cls) => h('marker', { id, class: cls, viewBox: '0 0 8 8', markerWidth: 8, markerHeight: 8, refX: 7, refY: 4, orient: 'auto', markerUnits: 'userSpaceOnUse' }, h('path', { d: 'M0,0.5 L8,4 L0,7.5 z' }));
    svg.append(h('defs', {}, tip(mid, 'tip'), tip(mid + 'h', 'tip hit')));
    const later = n => /\blater\b/.test(n.cls || '');
    nodes.forEach(n => (n.src || []).forEach((s, i) => { const a = by.get(s);
      const x1 = x.get(s), y1 = y(a) + NH(a), x2 = x.get(n.id) + (i - (n.src.length - 1) / 2) * 10, y2 = y(n);
      let px = x1, py = y1, path = `M${x1},${y1}`;
      (route.get(n.id + '~' + i) || []).forEach(id => { const dx = x.get(id), top = 12 + depth.get(id) * RH - 8, bot = top + 66, c = (py + top) / 2;
        path += ` C${px},${c} ${dx},${c} ${dx},${top} L${dx},${bot}`; px = dx; py = bot; });
      const m = (py + y2) / 2; path += ` C${px},${m} ${x2},${m} ${x2},${y2}`;
      const ec = (n.ecls || [])[i] || '';
      edges.append(h('path', { class: 'edge' + (ec ? ' ' + ec : '') + (later(n) || later(a) ? ' later' : ''), 'data-to': n.id, 'data-from': s, 'marker-end': `url(#${mid}${/\bhit\b/.test(ec) ? 'h' : ''})`, d: path })); }));
    nodes.forEach(n => { const w = NW(n), X = x.get(n.id) - w / 2, Y = y(n);
      const g = h('g', { class: 'node ' + (n.cls || '') + (n.src && n.src.length ? '' : ' const'), 'data-n': n.id });
      g.append(h('rect', { x: X, y: Y, width: w, height: NH(n), rx: 6 }));
      g.append(h('text', { x: x.get(n.id), y: Y + 22, 'text-anchor': 'middle', text: n.op }));
      if (n.sub) g.append(h('text', { class: 'sub' + (n.subcls ? ' ' + n.subcls : ''), x: x.get(n.id), y: Y + 40, 'text-anchor': 'middle', text: n.sub }));
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
      for (const t of toks) if (t.includes('=')) attrs.push(t); else if (t.startsWith('%')) src.push(names[t.slice(1)] ?? node(t, null, []));
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

  function trace(fig, text, { title = 'Step through the program', args = {}, edit = false } = {}) {
    const I = x => x | 0;
    const OPS = { add: (a, b) => I(a + b), mul: (a, b) => Math.imul(a, b), max: (a, b) => Math.max(a, b), xor: (a, b) => a ^ b,
      div: (a, b) => (b === 0 ? -1 : I(Math.floor(a / b))), mod: (a, b) => (b === 0 ? a : I(a - Math.floor(a / b) * b)), cmplt: (a, b) => a < b };
    const nameOf = l => (l.match(/^\s*%(\w+)\s*=/) || [])[1];
    let src = text.replace(/\s+$/, ''), lines, full, counts, vals, k = 0, pending = false, editing = false, guess = true;
    const parse = () => {
      lines = src.split('\n').filter(l => nameOf(l.split('#')[0]));
      full = parseUir(lines.join('\n'));
      counts = lines.map((_, i) => parseUir(lines.slice(0, i + 1).join('\n')).nodes.length);
      vals = new Map();
      for (const n of full.nodes) {
        const a = n.src.map(x => vals.get(x)), slot = (/slot=(\d+)/.exec(n.sub || '') || [])[1];
        vals.set(n.id, n.op === 'param' ? args[slot] : !n.src.length ? (/^-?\d+$/.test(n.op) ? I(+n.op) : n.op === 'true' ? true : n.op === 'false' ? false : undefined)
          : a.some(v => v === undefined) || !OPS[n.op] || a.length !== 2 ? undefined : OPS[n.op](...a));
      }
    };
    const shown = i => (i < 0 ? 0 : counts[i]);
    const own = i => full.names[nameOf(lines[i])];
    const fresh = i => full.nodes.slice(shown(i - 1), shown(i)).map(n => n.id);
    const prev = h('button', { class: 'btn', type: 'button', text: 'Back' }), next = h('button', { class: 'btn primary', type: 'button', text: 'Next' });
    const count = h('span', { class: 'count' }), codeEl = h('div', { class: 'tr-code' }), pic = h('div', { class: 'tr-pic' }), cap = h('div', { class: 'cap', 'aria-live': 'polite' });
    const box = h('input', { type: 'checkbox' }); box.checked = true; box.onchange = () => { guess = box.checked; };
    const editB = edit ? h('button', { class: 'btn', type: 'button', text: 'Edit' }) : null;
    fig.classList.add('trace');
    fig.replaceChildren(h('div', { class: 'head' }, h('span', { class: 'title', text: title }),
      h('span', { class: 'ctl' }, h('label', { class: 'tr-opt' }, box, 'Guess first'), editB, count, prev, next)),
      h('div', { class: 'body' }, h('div', { class: 'split' }, codeEl, pic)), cap);
    const lit = (i, on) => {
      if (i == null || i < 0 || i >= lines.length) return;
      const ids = new Set([own(i), ...fresh(i)]);
      codeEl.children[i]?.classList.toggle('lit', on);
      pic.querySelectorAll('[data-n]').forEach(g => { if (ids.has(g.dataset.n)) g.classList.toggle('lit', on); });
      pic.querySelectorAll('[data-to]').forEach(e => { if (e.dataset.to === own(i)) e.classList.toggle('lit', on); });
    };
    const lineOf = id => { const i = lines.findIndex((_, j) => fresh(j).includes(id)); return i < 0 ? lines.findIndex((_, j) => own(j) === id) : i; };
    const say = v => String(v);
    const show = () => {
      const n = lines.length;
      if (editing) {
        const ta = h('textarea', { class: 'tr-edit', spellcheck: 'false', 'aria-label': 'Program text', rows: Math.max(4, n + 1) }); ta.value = src;
        ta.oninput = () => { src = ta.value; parse(); k = lines.length; drawPic(); };
        codeEl.replaceChildren(ta);
      } else {
        codeEl.replaceChildren(...lines.map((l, i) => h('button', { type: 'button', class: 'tr-line' + (i === k - 1 ? ' cur' : i >= k ? ' later' : ''), text: l.trim(), 'aria-current': i === k - 1 ? 'step' : null,
          onclick: () => { const j = i + 1; pending = (j > k || (j === k && pending)) && asks(j); k = j; show(); }, onmouseenter: () => lit(i, true), onmouseleave: () => lit(i, false), onfocus: () => lit(i, true), onblur: () => lit(i, false) })));
      }
      drawPic();
      count.textContent = editing ? '' : `line ${k} of ${n}`;
      prev.disabled = editing || k === 0; next.disabled = editing || (k === n && !pending);
      if (editB) editB.textContent = editing ? 'Done' : 'Edit';
      if (editing) { cap.textContent = 'Type in the box. The picture follows every change.'; return; }
      if (!k) { cap.textContent = n ? 'Press Next to run the first line.' : 'No lines yet. Press Edit to write a program.'; return; }
      const id = own(k - 1), v = vals.get(id), made = fresh(k - 1).includes(id), line = lines[k - 1].trim();
      if (pending) {
        const inp = h('input', { 'aria-label': 'your guess', inputmode: 'numeric', autocomplete: 'off' });
        const go = () => { const ok = fillMatch([say(v)], inp.value); pending = false; show(); cap.prepend(h('strong', { text: ok ? 'Yes. ' : 'Not quite. ' })); };
        inp.onkeydown = e => { if (e.key === 'Enter') go(); };
        cap.replaceChildren(h('div', { class: 'tr-ask' }, h('span', {}, 'What value does ', h('code', { text: line }), ' make?'), inp,
          h('button', { class: 'btn', type: 'button', text: 'Check', onclick: go }), h('button', { class: 'btn quiet', type: 'button', text: 'Show me', onclick: () => { pending = false; show(); } })));
        inp.focus({ preventScroll: true });
        return;
      }
      cap.replaceChildren(h('span', {}, `Line ${k}: `, h('code', { text: line }),
        !made ? ' makes no new box. That value already exists, so this line reuses it.' : v === undefined ? ' adds a box.' : ` makes ${say(v)}.`));
    };
    const drawPic = () => {
      const lim = editing ? full.nodes.length : shown(k - 1), cur = !editing && k ? own(k - 1) : null;
      if (!full.nodes.length) { pic.replaceChildren(h('p', { class: 'muted', text: 'No lines yet.' })); return; }
      const label = (n, i) => (i >= lim ? ' ' : n.id === cur && pending ? '= ?' : vals.get(n.id) === undefined ? (n.op === 'param' ? 'input' : ' ') : (n.op === 'param' ? 'input = ' : '= ') + say(vals.get(n.id)));
      const svg = graph(full.nodes.map((n, i) => ({ ...n, sub: n.src.length || n.op === 'param' ? label(n, i) : n.sub, subcls: 'v',
        cls: i >= lim ? 'later' : n.id === cur ? 'hit' : '' })));
      svg.setAttribute('aria-label', `The program drawn as boxes and arrows, ${Math.min(lim, full.nodes.length)} of ${full.nodes.length} boxes shown`);
      svg.querySelectorAll('[data-n]').forEach(g => { const i = lineOf(g.dataset.n); g.onmouseenter = () => lit(i, true); g.onmouseleave = () => lit(i, false); });
      pic.replaceChildren(svg, lim === 0 ? h('p', { class: 'muted tr-hint', text: 'The picture appears here, one box at a time.' }) : '');
    };
    const asks = j => { const id = own(j - 1); return guess && vals.get(id) !== undefined && fresh(j - 1).includes(id) && full.nodes.find(n => n.id === id).src.length > 0; };
    next.onclick = () => {
      if (pending) { pending = false; show(); return; }
      if (k >= lines.length) return;
      k++;
      pending = asks(k);
      show();
    };
    prev.onclick = () => { if (k > 0) { pending = false; k--; show(); } };
    if (editB) editB.onclick = () => { editing = !editing; pending = false; parse(); k = lines.length; show(); };
    parse(); show();
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
      if (/^[-+]?\d{1,3}(,\d{3})+(\.\d+)?$/.test(x)) x = x.replace(/,/g, '');
      if (/^[-+]?(inf|infinity)$/.test(x)) return x.startsWith('-') ? -Infinity : Infinity;
      if (/^[-+]?0x[0-9a-f]+$/.test(x)) return (x.startsWith('-') ? -1 : 1) * parseInt(x.replace(/^[-+]/, ''), 16);
      return /^[-+]?(\d+\.?\d*|\.\d+)(e[-+]?\d+)?$/.test(x) ? Number(x) : null;
    };
    const t = norm(typed), tn = num(t);
    const flat = x => x.replace(/[\[\]()]/g, ' ').replace(/,|\bby\b/g, ' ').replace(/\s+/g, ' ').trim();   // shapes: (4, 3) = [4 3] = 4 by 3
    return accepted.some(a => { a = norm(a); return a === t || (tn !== null && num(a) === tn) || (flat(a) !== '' && flat(a) === flat(t)); });
  }

  function quizId(pageKey, q) {
    const text = (q.textContent || '').replace(/\s+/g, ' ').trim();
    let x = 5381;
    for (let i = 0; i < text.length; i++) x = ((x * 33) ^ text.charCodeAt(i)) >>> 0;
    return `${pageKey}#${x.toString(36)}`;
  }

  function quizzes(root = document) {
    const all = [...root.querySelectorAll('.quiz')]; let first = 0, done = 0;
    const page = here(); const pageKey = page ? page[1][0] : location.pathname;
    const lessonKey = root === document && page && page[1][2] ? page[1][0] : null;
    all.forEach(q => { if (!q.dataset.qid) q.dataset.qid = quizId(pageKey, q); });
    // the score counts only quizzes on the reader's language track (ids above still index every quiz, so they stay stable)
    const n = all.filter(q => !q.closest(track() === 'python' ? '.only-ocaml' : '.only-python')).length;
    const before = new Set(lessonKey ? all.filter(q => store.get('cc-q:' + q.dataset.qid)).map(q => q.dataset.qid) : []);
    const tally = () => { const left = all.filter(q => onPage(q) && !q.classList.contains('done') && !before.has(q.dataset.qid)).length;
      document.querySelectorAll('.score').forEach(s => (s.textContent = `${first} / ${n} first try` + (left ? ` · ${left} to go` : done < n ? ' · the rest answered on an earlier visit' : ''))); };
    all.forEach(q => {
      const hints = [...q.querySelectorAll('.hint')]; let tries = 0, seen = 0, nudged = false;
      const msg = h('span', { class: 'qmsg', 'aria-live': 'polite' });
      const hintB = hints.length ? h('button', { class: 'btn', type: 'button', text: hints.length > 1 ? `Hint 1 of ${hints.length}` : 'Hint' }) : null;
      const showB = h('button', { class: 'btn quiet', type: 'button', text: 'Show answer' });
      const bar = h('div', { class: 'qactions' }, hintB, showB, msg);
      if (before.has(q.dataset.qid)) { msg.textContent = 'You answered this before. Try it again from memory.'; msg.className = 'qmsg'; }
      const why0 = q.querySelector('.why'); if (why0) why0.before(bar); else q.append(bar);
      const mc = !!q.dataset.answer, opts = [...q.querySelectorAll('.opts button')];
      const inp = q.querySelector('.fill input'), checkB = q.querySelector('.fill button');
      const ans = mc ? null : (q.dataset.fill || '').split('|').map(x => x.trim().toLowerCase());
      const finish = (how) => {             // how: 'first' | 'later' | 'shown'
        if (q.classList.contains('done')) return;
        q.classList.add('done'); done++; if (how === 'first') first++;
        try { if (how === 'first') localStorage.removeItem('cc-missed:' + q.dataset.qid); else localStorage.setItem('cc-missed:' + q.dataset.qid, '1'); } catch {}
        schedule(q.dataset.qid, how === 'first');
        opts.forEach(o => { o.disabled = true; if (o.dataset.k === q.dataset.answer) o.classList.add('right'); });
        if (inp) { inp.disabled = checkB.disabled = true; if (how === 'shown') inp.value = q.dataset.fill.split('|')[0].trim(); inp.classList.toggle('good', how !== 'shown'); }
        bar.remove(); hints.forEach(x => x.classList.add('shown'));
        const w = q.querySelector('.why') || q.appendChild(h('div', { class: 'why' }));
        w.prepend(h('span', { class: 'verdict ' + (how === 'shown' ? 'shown' : 'ok'), text: how === 'first' ? 'Right.' : how === 'later' ? `Right, on try ${tries + 1}.` : 'Answer shown.' }));
        tally();
        if (lessonKey && !isDone(lessonKey) && all.filter(onPage).every(x => store.get('cc-q:' + x.dataset.qid))) setDone(lessonKey, true); else changed();
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
  const plain = t => String(t).replace(/<code>([\s\S]*?)<\/code>/g, '`$1`').replace(/<\/?(?:b|strong|em|i|p)>/g, '').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
  const rich = t => { const e = h('span'); plain(t).split(/(`[^`]+`)/).forEach(part => e.append(part.startsWith('`') && part.endsWith('`') && part.length > 1 ? h('code', { text: part.slice(1, -1) }) : part)); return e; };

  // ---- exercises ----
  const KEYMAPS = [['default', 'Default'], ['vim', 'Vim'], ['emacs', 'Emacs'], ['sublime', 'Sublime']];
  const editors = new Set(), selects = new Set();
  const keymap = () => store.get('cc-keymap') || 'default';
  function setKeymap(k) { store.set('cc-keymap', k); editors.forEach(cm => { cm.setOption('keyMap', k); cm.getWrapperElement().dispatchEvent(new Event('cc-keymap')); }); selects.forEach(s => s.paint(k)); document.dispatchEvent(new Event('cc-keymap')); }
  function keymapSelect() {
    const s = segPick('Key bindings for the site and the code editors', KEYMAPS, keymap(), setKeymap);
    selects.add(s); return s;
  }
  function siteKeys() {
    const on = () => keymap() !== 'default';
    const inEditor = t => t && t.closest && t.closest('.CodeMirror');
    const typing = t => t && t.closest && !inEditor(t) && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName));
    const shown = el => { const r = el.getBoundingClientRect(); return r.width > 1 && r.height > 1 && getComputedStyle(el).visibility !== 'hidden'; };
    let lastCM = null, seq = '', seqT = 0, escT = 0, hints = null, layer = null;
    document.addEventListener('focusin', e => { const w = inEditor(e.target); if (w && w.CodeMirror) lastCM = w.CodeMirror; });

    const scroll = (dy, smooth = true) => scrollBy({ top: dy, behavior: smooth ? 'smooth' : 'auto' });
    const line = () => scroll(64, false), lineUp = () => scroll(-64, false);
    const half = () => scroll(innerHeight / 2), halfUp = () => scroll(-innerHeight / 2);
    const page = () => scroll(innerHeight * 0.85), pageUp = () => scroll(-innerHeight * 0.85);
    const top = () => scrollTo({ top: 0, behavior: 'smooth' });
    const bottom = () => scrollTo({ top: document.documentElement.scrollHeight, behavior: 'smooth' });
    const part = d => {
      const nav = document.querySelector('.stepnav');
      if (nav && !nav.hidden) {
        const b = d > 0 ? nav.querySelector('.btn.primary') : nav.querySelector('.btn:not(.primary)');
        if (b && !b.hidden && !b.disabled) return b.click();
        return d > 0 ? bottom() : top();
      }
      const hs = [...document.querySelectorAll('main h2')].filter(shown), y = 72;
      const t = d > 0 ? hs.find(x => x.getBoundingClientRect().top > y + 8) : hs.filter(x => x.getBoundingClientRect().top < y - 8).pop();
      if (t) t.scrollIntoView({ block: 'start', behavior: 'smooth' }); else (d > 0 ? bottom : top)();
    };
    const lesson = d => { const a = [...document.querySelectorAll('main nav.pager a')]; const t = d > 0 ? a[a.length - 1] : a[0]; if (t) location.href = t.href; };
    const editor = () => {
      const all = [...document.querySelectorAll('.CodeMirror')].filter(shown);
      const inView = all.filter(w => { const r = w.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight; });
      const w = (lastCM && all.includes(lastCM.getWrapperElement()) && lastCM.getWrapperElement()) || inView[0] || all[0];
      if (!w) return;
      w.scrollIntoView({ block: 'center', behavior: 'smooth' }); w.CodeMirror.focus();
    };
    const search = () => {
      const s = document.querySelector('.side .search input'); if (!s) return;
      if (!shown(s)) document.querySelector('.topbar .menu')?.click();
      setTimeout(() => s.focus(), 60);
    };

    const leave = cm => {
      lastCM = cm; cm.getInputField().blur(); setTimeout(() => { if (inEditor(document.activeElement)) document.activeElement.blur(); }, 0);
      const w = cm.getWrapperElement(); w.classList.add('kb-left'); setTimeout(() => w.classList.remove('kb-left'), 900);
    };
    addEventListener('keydown', e => {
      if (!on() || e.key !== 'Escape') return;
      const w = inEditor(e.target);
      if (!w) { if (typing(e.target) && !layer) e.target.blur(); return; }
      const cm = w.CodeMirror; if (!cm) return;
      const km = keymap(), out = () => { e.preventDefault(); e.stopPropagation(); leave(cm); };
      if (km === 'vim') { const v = cm.state.vim; if (v && !v.insertMode && !v.visualMode) out(); return; }
      if (km === 'emacs') { const now = Date.now(); if (now - escT < 700) { escT = 0; out(); } else escT = now; return; }
      out();
    }, true);

    const LET = 'asdfghjklqwertyuiopzxcvbnm';
    function showHints() {
      const sel = 'a[href], button, input, textarea, select, summary, .CodeMirror, [tabindex]:not([tabindex="-1"])';
      const els = [...document.querySelectorAll(sel)].filter(el => {
        if (el.tagName === 'TEXTAREA' && inEditor(el)) return false;
        if (inEditor(el) && !el.classList.contains('CodeMirror')) return false;
        if (el.disabled || el.closest('[hidden], [inert]')) return false;
        const r = el.getBoundingClientRect();
        return r.width > 2 && r.height > 2 && r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth && getComputedStyle(el).visibility !== 'hidden';
      });
      if (!els.length) return;
      const two = els.length > LET.length;
      const box = h('div', { class: 'kb-hints', 'aria-hidden': 'true' });
      const items = els.map((el, i) => {
        const code = two ? LET[Math.floor(i / LET.length) % LET.length] + LET[i % LET.length] : LET[i];
        const r = el.getBoundingClientRect();
        const tag = h('span', { class: 'kb-hint', text: code, style: `left:${Math.max(0, r.left)}px;top:${Math.max(0, r.top)}px` });
        box.append(tag); return { el, code, tag };
      });
      document.body.append(box);
      hints = { box, items, typed: '' };
    }
    const closeHints = () => { if (hints) hints.box.remove(); hints = null; };
    const activate = el => {
      if (el.classList.contains('CodeMirror')) { el.CodeMirror.focus(); return; }
      if (/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName)) { el.focus(); return; }
      el.focus({ preventScroll: true }); el.click();
    };
    const hintKey = e => {
      e.preventDefault(); e.stopPropagation();
      if (e.key === 'Escape') return closeHints();
      if (e.key === 'Backspace') hints.typed = hints.typed.slice(0, -1);
      else if (e.key.length === 1 && LET.includes(e.key.toLowerCase())) hints.typed += e.key.toLowerCase();
      else return;
      const left = hints.items.filter(it => it.code.startsWith(hints.typed));
      hints.items.forEach(it => { it.tag.hidden = !it.code.startsWith(hints.typed); it.tag.classList.toggle('part', !!hints.typed && it.code.startsWith(hints.typed)); });
      if (!left.length) return closeHints();
      if (left.length === 1 && left[0].code === hints.typed) { const el = left[0].el; closeHints(); activate(el); }
    };

    const fuzzy = (q, s) => { q = q.toLowerCase(); s = s.toLowerCase(); let i = 0; for (const c of s) if (c === q[i]) i++; return i === q.length; };
    function palette(title, list, choose) {
      const input = h('input', { type: 'text', 'aria-label': title, placeholder: title, autocomplete: 'off', spellcheck: 'false' });
      const ul = h('ul', { class: 'kb-list', role: 'listbox' });
      let shown_ = [], sel = 0;
      const paint = () => {
        const q = input.value.trim().toLowerCase(), rank = it => { const t = it.text.toLowerCase(), u = (it.sub || '').toLowerCase();
          return !q ? 0 : t.includes(q) ? (t.split(' ').slice(1).join(' ').startsWith(q) ? 0 : 1) : u.includes(q) ? 2 : fuzzy(q, it.text) ? 3 : fuzzy(q, it.text + ' ' + u) ? 4 : 9; };
        shown_ = list.map((it, i) => [rank(it), i, it]).filter(r => r[0] < 9).sort((x, y) => x[0] - y[0] || x[1] - y[1]).map(r => r[2]).slice(0, 60);
        sel = Math.min(sel, Math.max(0, shown_.length - 1));
        ul.replaceChildren(...shown_.map((it, i) => h('li', { role: 'option', class: i === sel ? 'on' : '', 'aria-selected': String(i === sel), onmousedown: ev => { ev.preventDefault(); pick(i); } },
          h('span', { class: 'kb-t', text: it.text }), it.sub ? h('span', { class: 'kb-s', text: it.sub }) : null)));
        ul.querySelector('.on')?.scrollIntoView({ block: 'nearest' });
      };
      const pick = i => { const it = shown_[i]; closeLayer(); if (it) choose(it); };
      input.addEventListener('input', () => { sel = 0; paint(); });
      input.addEventListener('keydown', ev => {
        const k = ev.key, c = ev.ctrlKey;
        if (k === 'ArrowDown' || (c && (k === 'n' || k === 'j'))) { ev.preventDefault(); sel = Math.min(sel + 1, shown_.length - 1); paint(); }
        else if (k === 'ArrowUp' || (c && (k === 'p' || k === 'k'))) { ev.preventDefault(); sel = Math.max(sel - 1, 0); paint(); }
        else if (k === 'Enter') { ev.preventDefault(); pick(sel); }
        else if (k === 'Escape') { ev.preventDefault(); closeLayer(); }
      });
      openLayer(h('div', { class: 'kb-box', role: 'dialog', 'aria-modal': 'true', 'aria-label': title }, input, ul));
      paint(); input.focus();
    }
    const lessons = () => {
      const root = ROOT(), here = location.pathname.replace(/\.html$/, '');
      const list = NAV.flatMap(g => g.items.filter(onTrackItem).map(([href, t, n]) => ({ text: (n ? n + ' ' : '') + t, sub: g.title, href: root + href })));
      palette('Go to a lesson', list, it => { if (new URL(it.href, location.href).pathname.replace(/\.html$/, '') !== here) location.href = it.href; });
    };
    const sections = () => {
      const hs = [...document.querySelectorAll('main h2')].filter(x => x.id);
      if (!hs.length) return;
      palette('Go to a part of this page', hs.map((x, i) => ({ text: x.textContent, sub: 'Part ' + (i + 1), id: x.id })), it => {
        if (location.hash === '#' + it.id) dispatchEvent(new HashChangeEvent('hashchange')); else location.hash = it.id;
        setTimeout(() => document.getElementById(it.id)?.scrollIntoView({ block: 'start' }), 30);
      });
    };

    const VIM = [['j', 'Scroll down', line], ['k', 'Scroll up', lineUp], ['d', 'Half a page down', half], ['u', 'Half a page up', halfUp],
      ['gg', 'Top of the page', top], ['G', 'Bottom of the page', bottom], ['l', 'Next part of the lesson', () => part(1)], ['h', 'Previous part', () => part(-1)],
      [']]', 'Next lesson', () => lesson(1)], ['[[', 'Previous lesson', () => lesson(-1)], ['f', 'Label every link and button, then type a label to click it', showHints],
      ['o', 'Go to any lesson by name', lessons], ['s', 'Go to a part of this page', sections], ['/', 'Search the lessons', search],
      ['i', 'Into the code editor', editor], ['H', 'Back in history', () => history.back()], ['L', 'Forward in history', () => history.forward()], ['?', 'Show these keys', () => help()]];
    const EMACS = [['C-n', 'Scroll down', line], ['C-p', 'Scroll up', lineUp], ['C-v', 'Page down', page], ['M-v', 'Page up', pageUp],
      ['SPC', 'Page down', page], ['Backspace', 'Page up', pageUp], ['M-<', 'Top of the page', top], ['M->', 'Bottom of the page', bottom],
      ['n', 'Next part of the lesson', () => part(1)], ['p', 'Previous part', () => part(-1)], [']', 'Next lesson', () => lesson(1)], ['[', 'Previous lesson', () => lesson(-1)],
      ['f', 'Label every link and button, then type a label to click it', showHints], ['g', 'Go to any lesson by name', lessons], ['i', 'Go to a part of this page', sections],
      ['C-s', 'Search the lessons', search], ['e', 'Into the code editor', editor], ['l', 'Back in history', () => history.back()], ['?', 'Show these keys', () => help()]];
    const SUBLIME = [['C-p', 'Go to any lesson by name', lessons], ['C-r', 'Go to a part of this page', sections], ['C-;', 'Label every link and button, then type a label to click it', showHints],
      ['C-]', 'Next part of the lesson', () => part(1)], ['C-[', 'Previous part', () => part(-1)], ['M-ArrowDown', 'Next part of the lesson', () => part(1)], ['M-ArrowUp', 'Previous part', () => part(-1)],
      ['C-i', 'Into the code editor', editor], ['C-k', 'Search the lessons', search], ['F1', 'Show these keys', () => help()], ['?', 'Show these keys', () => help()]];
    const MAPS = { vim: VIM, emacs: EMACS, sublime: SUBLIME };
    const LEAVE = { vim: 'Escape in normal mode', emacs: 'Escape twice', sublime: 'Escape' };
    const show = k => k.replace('SPC', 'Space').replace('C-', 'Ctrl+').replace('M-', 'Alt+').replace('Arrow', '');

    function help() {
      const km = keymap(), rows = MAPS[km];
      openLayer(h('div', { class: 'kb-box kb-help', role: 'dialog', 'aria-modal': 'true', 'aria-label': 'Keyboard keys', tabindex: '-1' },
        h('p', { class: 'kb-head', text: `${KEYMAPS.find(x => x[0] === km)[1]} keys for the whole site` }),
        h('table', {}, rows.map(([k, d]) => h('tr', {}, h('td', {}, h('kbd', { text: show(k) })), h('td', { text: d })))),
        h('p', { class: 'kb-note', text: `In a code editor your keys go to the editor. ${LEAVE[km]} leaves it, and ${show(km === 'vim' ? 'i' : km === 'emacs' ? 'e' : 'C-i')} goes back in. Turn these off by choosing Default under Keys in the sidebar.` })));
      layer.querySelector('.kb-help').focus();
    }
    function openLayer(box) {
      closeLayer(); closeHints();
      layer = h('div', { class: 'kb-layer', onmousedown: e => { if (e.target === layer) closeLayer(); } }, box);
      layer.addEventListener('keydown', e => { if (e.key === 'Escape' || (e.key === '?' && box.classList.contains('kb-help'))) { e.preventDefault(); e.stopPropagation(); closeLayer(); } });
      document.body.append(layer);
    }
    function closeLayer() { if (layer) { layer.remove(); layer = null; } }

    const combo = e => (e.ctrlKey ? 'C-' : '') + (e.altKey ? 'M-' : '') + (e.metaKey ? 's-' : '') + (e.key === ' ' ? 'SPC' : e.key);
    addEventListener('keydown', e => {
      if (!on() || e.isComposing) return;
      if (hints) return hintKey(e);
      if (layer || e.defaultPrevented) return;
      const t = e.target;
      if (inEditor(t) || typing(t)) return;
      if (['Shift', 'Control', 'Alt', 'Meta'].includes(e.key)) return;
      const k = combo(e), map = MAPS[keymap()];
      if ((k === 'SPC' || k === 'Enter') && t !== document.body && t.closest && t.closest('a, button, summary, [tabindex]')) return;
      if (Date.now() - seqT > 900) seq = '';
      const tryKey = s => map.find(([key]) => key === s);
      const want = seq + k, hit = tryKey(want);
      const more = map.some(([key]) => key.length > want.length && key.startsWith(want));
      if (hit && !more) { e.preventDefault(); seq = ''; hit[2](); return; }
      if (more) { e.preventDefault(); seq = want; seqT = Date.now(); return; }
      seq = '';
      const alone = tryKey(k);
      if (alone) { e.preventDefault(); alone[2](); }
    });

    const chip = h('button', { type: 'button', class: 'kb-chip', title: 'Keyboard keys for the whole site', onclick: () => help() });
    const paintChip = () => { chip.hidden = !on(); chip.textContent = on() ? `${KEYMAPS.find(x => x[0] === keymap())[1]} keys · ${show(keymap() === 'sublime' ? 'F1' : '?')}` : ''; };
    const bar = document.querySelector('.topbar'); if (bar) bar.insertBefore(chip, bar.querySelector('.runner') || null);
    document.addEventListener('cc-keymap', paintChip); paintChip();
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
        if (s.match(/\b(i32|i8|f32|bool|void)\b/)) return 'type';
        if (s.match(/-?(?:0x[0-9a-fA-F]+|(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?)|\b(inf|nan|true|false)\b/)) return 'number';
        if (s.match(/[a-z_]+/)) return 'keyword';
        s.next(); return null; }, lineComment: '#' })); return window.CodeMirror; });
  }
  const MODE = { ocaml: 'text/x-ocaml', c: 'text/x-csrc', uir: 'uir', python: 'text/x-python' }, LANG = { ocaml: 'OCaml', c: 'C', uir: '.uir', python: 'Python' };

  // ---- in-browser Python / .uir runner (Pyodide Web Worker) ----
  let pyWorker = null, pySeq = 0, pyReady = false;
  function browserRun(ex, code, submit, onStatus) {
    return new Promise(resolve => {
      if (!pyWorker) pyWorker = new Worker(new URL(ROOT() + 'assets/py-worker.js', location.href));
      const jobId = ++pySeq;
      const ms = pyReady ? 12000 : 45000;
      const timer = setTimeout(() => {
        try { pyWorker.terminate(); } catch {}
        pyWorker = null; pyReady = false;
        resolve({ ok: false, error: `timed out after ${ms / 1000}s (infinite loop, or slow connection loading Python?)` });
      }, ms);
      const onMsg = ev => {
        const d = ev.data;
        if (d.type === 'status') { if (onStatus) onStatus(d.text); return; }
        if (d.id !== jobId) return;
        clearTimeout(timer);
        pyWorker.removeEventListener('message', onMsg);
        pyWorker.removeEventListener('error', onErr);
        if (d.type === 'result') { pyReady = true; resolve(d.res); }
        else resolve({ ok: false, error: 'Browser runner failed: ' + d.message + '\n(You can also run locally with python tools/serve.py.)' });
      };
      const onErr = () => {
        clearTimeout(timer);
        try { pyWorker.terminate(); } catch {}
        pyWorker = null; pyReady = false;
        resolve({ ok: false, error: 'Browser runner could not start (offline?). Run locally with python tools/serve.py.' });
      };
      pyWorker.addEventListener('message', onMsg);
      pyWorker.addEventListener('error', onErr);
      const uircUrl = new URL(ROOT() + 'data/uirc.py', location.href).href;
      pyWorker.postMessage({ id: jobId, ex, code, submit, uircUrl });
    });
  }

  async function exercises() {
    const els = [...document.querySelectorAll('.exercise[data-ex]')];
    if (!els.length) return;
    // each exercise in the reader's language: a Python version where the lesson has one
    const pick = e => (track() === 'python' && e.dataset.exPy) || e.dataset.ex;
    const ids = els.map(pick), page = here(), pageKey = page && 'cc-prog:' + page[1][0];
    const record = () => { if (!pageKey) return; const s = ids.filter(i => store.get('cc-solved:' + i)).length, t = ids.length;
      store.set(pageKey, JSON.stringify({ s, t })); changed(); };   // keep the sidebar count live, once something is solved
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
      if (stuck) prompt.append(stuck.el);
      // With the local runner (tools/serve.py), every language runs on your machine. On the hosted site,
      // Python and .uir exercises run right in the browser (WebAssembly); C and OCaml compare against the answer.
      const canBrowser = !r && location.protocol.startsWith('http') && typeof Worker !== 'undefined' && (ex.lang === 'python' || ex.lang === 'uir') && Array.isArray(ex.tests);
      const noTool = r && ex.lang === 'ocaml' && !r.ocaml ? 'OCaml isn’t installed on this machine (lesson 0.6 shows how), so its tests can’t run here.'
        : r && ex.lang === 'c' && !r.cc ? 'No C compiler was found on this machine (lesson 0.1 shows how to get one), so its tests can’t run here.' : null;
      const canRun = !!((r && !noTool) || canBrowser);
      const edDiv = h('div', { class: 'ex-editor' });
      const out = h('div', { class: 'ex-out' }, h('span', { class: 'hint', text: noTool ? noTool + ' Write your answer, then compare it with the reference answer.'
        : r ? 'Run checks the examples. Submit runs every test.'
        : canBrowser ? 'Runs right in your browser (no setup). Run checks the examples. Submit runs every test.'
        : 'Write your answer, then compare it with the reference answer. Running C or OCaml tests needs python tools/serve.py.' }));
      const mode = h('span'), keys = h('span', { text: canRun ? 'Ctrl+Enter run · Ctrl+Shift+Enter submit' : 'Ctrl+Enter compare' });
      const runB = h('button', { class: 'btn', type: 'button', text: 'Run' }), subB = h('button', { class: 'btn primary', type: 'button', text: 'Submit' });
      const cmpB = h('button', { class: 'btn primary', type: 'button', text: 'Compare with answer' });
      const resetB = h('button', { class: 'btn', type: 'button', text: 'Reset', title: 'Back to the starter code' });
      work.append(h('div', { class: 'ex-bar' }, h('span', { class: 'lang', text: LANG[ex.lang] }), keymapSelect(), resetB, ...(canRun ? [runB, subB] : [cmpB])),
        edDiv, h('div', { class: 'ex-status' }, mode, keys), out);
      let CM;
      try { CM = await loadCM(); } catch (e) { edDiv.append(h('div', { class: 'ex-offline', text: 'Editor failed to load: ' + e.message })); continue; }
      const draftKey = 'cc-code:' + id;
      const go = submit => canRun ? run(submit) : compare();
      cm = CM(edDiv, { value: store.get(draftKey) ?? ex.starter, mode: MODE[ex.lang], keyMap: keymap(), lineNumbers: true, indentUnit: 2, tabSize: 2,
        matchBrackets: true, autoCloseBrackets: true, styleActiveLine: !TOUCH, viewportMargin: Infinity, showCursorWhenSelecting: true,
        spellcheck: false, autocorrect: false, autocapitalize: false, lineWrapping: true, screenReaderLabel: 'Code editor',
        extraKeys: { 'Ctrl-Enter': () => go(false), 'Cmd-Enter': () => go(false), 'Shift-Ctrl-Enter': () => go(true), 'Shift-Cmd-Enter': () => go(true),
          Tab: c => c.somethingSelected() ? c.indentSelection('add') : c.replaceSelection('  ') } });
      editors.add(cm);
      if (stuck) stuck.init();
      edDiv.after(keybar(cm, ex.lang, () => go(false), canRun ? 'Run' : 'Compare'));
      const paintMode = () => (mode.textContent = keymap() === 'vim' ? '-- NORMAL --' : KEYMAPS.find(k => k[0] === keymap())[1] + ' keys');
      cm.on('vim-mode-change', e => (mode.textContent = '-- ' + (e.subMode ? e.subMode : e.mode).toUpperCase() + ' --'));
      cm.getWrapperElement().addEventListener('cc-keymap', paintMode); paintMode();
      cm.on('change', () => store.set(draftKey, cm.getValue()));
      resetB.onclick = () => { cm.setValue(ex.starter); cm.focus(); };
      async function run(submit) {
        runB.disabled = subB.disabled = true; out.replaceChildren(h('span', { class: 'hint', text: submit ? 'Running every test…' : 'Running examples…' }));
        let res;
        if (r) {
          try { res = await fetch(api('run'), { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Course-Runner': '1' },
            body: JSON.stringify({ id, code: cm.getValue(), submit }) }).then(x => x.json()); }
          catch (e) { res = { ok: false, error: 'The runner stopped responding. Is tools/serve.py still running?' }; }
        } else {
          res = await browserRun(ex, cm.getValue(), submit, msg => out.replaceChildren(h('span', { class: 'hint', text: msg })));
        }
        runB.disabled = subB.disabled = false;
        out.replaceChildren(...render(res, submit));
        if (submit && res.ok && res.passed === res.total) { store.set('cc-solved:' + id, '1'); solved.hidden = false; studied(); record();
          if (page && ids.every(i => store.get('cc-solved:' + i))) setDone(page[1][0], true); }
      }
      runB.onclick = () => run(false); subB.onclick = () => run(true);
      // Compare shows the answer's code, so the first time it asks once, as Show answer does.
      let warned = !!store.get('cc-peek:' + id);
      async function compare() {
        if (!ex.answer && r) try { ex.answer = await fetch(api('solution/' + id)).then(x => x.json()); } catch {}
        const ans = ex.answer && ex.answer.code;
        if (!ans) { out.replaceChildren(h('span', { class: 'hint', text: 'This exercise has no reference answer to compare with.' })); return; }
        if (!warned) { warned = true; cmpB.textContent = 'Compare anyway';
          out.replaceChildren(h('span', { class: 'hint', text: 'Comparing shows lines of the answer. Try a hint first if you want to keep the puzzle.' })); return; }
        cmpB.textContent = 'Compare again'; store.set('cc-peek:' + id, '1');
        out.replaceChildren(...diffView(cm.getValue(), ans, ex.lang), noTool ? h('p', { class: 'ex-note', text: noTool + ' Restart python tools/serve.py once it’s installed.' }) : offlineNote());
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
    const el = h('div', { class: 'ex-stuck' }, h('span', { class: 'label', text: 'Stuck?' }), list, h('div', { class: 'qactions' }, hints.length ? hintB : null, showB, msg), ansBox);
    return { el, init: () => { if (store.get('cc-peek:' + id)) reveal(); } };
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

  function termViz(kind) {
    const box = (x, y, w, ht, label, sub, hi) => {
      const g = h('g', {},
        h('rect', { x, y, width: w, height: ht, rx: 5, fill: hi ? 'var(--panel-2)' : 'var(--panel)', stroke: hi ? 'var(--good)' : 'var(--line-2)', 'stroke-width': hi ? 1.5 : 1 }),
        h('text', { x: x + w / 2, y: y + (sub ? 17 : ht / 2 + 4), 'text-anchor': 'middle', fill: hi ? 'var(--ink)' : 'var(--ink)', 'font-size': 11, 'font-weight': hi ? 600 : 500, text: label }));
      if (sub) g.append(h('text', { x: x + w / 2, y: y + 31, 'text-anchor': 'middle', fill: 'var(--ink-3)', 'font-size': 10, text: sub }));
      return g;
    };
    const arr = (x1, y1, x2, y2, hi) => h('line', { x1, y1, x2, y2, stroke: hi ? 'var(--good)' : 'var(--ink-3)', 'stroke-width': 1.4 });
    const txt = (x, y, text, fill = 'var(--ink-3)', anchor = 'start', sz = 10) => h('text', { x, y, fill, 'text-anchor': anchor, 'font-size': sz, text });

    if (kind === 'uop') return h('svg', { viewBox: '0 0 320 68', 'aria-hidden': 'true' },
      box(6, 6, 86, 40, 'op', 'ADD', true),
      box(102, 6, 122, 40, 'src (tuple)', '(%a, %b)', false),
      box(234, 6, 80, 40, 'arg', 'None / 5', false),
      txt(160, 62, '+ computed dtype (i32) & shape ()', 'var(--ink-3)', 'middle'));

    if (kind === 'tuple') return h('svg', { viewBox: '0 0 320 64', 'aria-hidden': 'true' },
      txt(12, 29, '(', 'var(--ink-3)', 'start', 18),
      box(26, 8, 64, 30, '[0] %a', null, true),
      box(98, 8, 64, 30, '[1] %b', null, false),
      txt(168, 29, ')', 'var(--ink-3)', 'start', 18),
      txt(186, 27, '≠ (%b, %a)', 'var(--ink-2)', 'start', 11),
      txt(160, 56, 'ordered · immutable · safe as a hash table key', 'var(--ink-3)', 'middle'));

    if (kind === 'dag') return h('svg', { viewBox: '0 0 320 92', 'aria-hidden': 'true' },
      txt(70, 12, 'Tree (copied)', 'var(--ink-3)', 'middle'),
      box(14, 20, 46, 22, 'add', null, false), box(78, 20, 46, 22, 'add', null, false),
      arr(37, 42, 62, 62), arr(101, 42, 76, 62),
      box(46, 62, 46, 22, 'mul', null, false),
      h('line', { x1: 152, y1: 10, x2: 152, y2: 84, stroke: 'var(--line)', 'stroke-width': 1 }),
      txt(238, 12, 'DAG (shared)', 'var(--good)', 'middle'),
      box(215, 20, 46, 22, 'add', null, true),
      h('path', { d: 'M228,42 C216,52 218,56 230,62', fill: 'none', stroke: 'var(--good)', 'stroke-width': 1.4 }),
      h('path', { d: 'M248,42 C260,52 258,56 246,62', fill: 'none', stroke: 'var(--good)', 'stroke-width': 1.4 }),
      box(215, 62, 46, 22, 'mul', null, false));

    if (kind === 'hash-consing') return h('svg', { viewBox: '0 0 320 68', 'aria-hidden': 'true' },
      box(6, 12, 98, 34, 'add(%x, 1)', 'new request', false),
      arr(104, 29, 124, 29),
      box(126, 12, 82, 34, 'cache', 'key lookup', false),
      arr(208, 29, 228, 29, true),
      box(230, 12, 84, 34, 'node #4', 'same object', true),
      txt(160, 62, 'hit: returns existing node instead of allocating a copy', 'var(--ink-3)', 'middle'));

    if (kind === 'memoization') return h('svg', { viewBox: '0 0 320 66', 'aria-hidden': 'true' },
      box(6, 10, 74, 32, 'visit(u)', null, false),
      arr(80, 26, 102, 26),
      box(104, 10, 88, 32, 'u in memo?', null, false),
      arr(192, 26, 214, 26, true),
      box(216, 10, 98, 32, 'memo[u]', 'skip work', true),
      txt(160, 58, 'turns 2^94 tree paths into 95 node evaluations', 'var(--ink-3)', 'middle'));

    if (kind === 'toposort') return h('svg', { viewBox: '0 0 320 60', 'aria-hidden': 'true' },
      box(8, 10, 54, 26, 'const 2', null, false), arr(62, 23, 76, 23),
      box(78, 10, 54, 26, 'const 3', null, false), arr(132, 23, 146, 23),
      box(148, 10, 64, 26, '%a = add', null, true), arr(212, 23, 226, 23, true),
      box(228, 10, 82, 26, '%b = mul', null, false),
      txt(160, 52, 'every source appears before every node that reads it', 'var(--ink-3)', 'middle'));

    if (kind === 'fixpoint') return h('svg', { viewBox: '0 0 320 66', 'aria-hidden': 'true' },
      box(8, 14, 72, 28, 'graph', null, false), arr(80, 28, 100, 28),
      box(102, 14, 96, 28, 'apply rules', null, true), arr(198, 28, 224, 28),
      box(226, 14, 86, 28, 'unchanged', null, false),
      h('path', { d: 'M150,42 C150,58 44,58 44,42', fill: 'none', stroke: 'var(--ink-3)', 'stroke-width': 1.2 }),
      txt(96, 61, 'changed? repeat', 'var(--ink-3)', 'middle'));

    if (kind === 'cache-line') return h('svg', { viewBox: '0 0 320 62', 'aria-hidden': 'true' },
      ...Array.from({ length: 8 }, (_, i) => box(8 + i * 38, 10, 34, 24, `a[${i}]`, null, i === 0)),
      txt(160, 52, 'reading a[0] fetches the entire 64-byte line into L1 cache', 'var(--ink-3)', 'middle'));

    if (kind === 'coalescing') return h('svg', { viewBox: '0 0 320 74', 'aria-hidden': 'true' },
      txt(8, 12, 'Coalesced (adjacent threads → 1 fetch)', 'var(--good)'),
      ...Array.from({ length: 8 }, (_, i) => box(8 + i * 38, 18, 34, 18, `t${i}`, null, true)),
      txt(8, 50, 'Strided (gaps → many wasted fetches)', 'var(--ink-3)'),
      ...Array.from({ length: 8 }, (_, i) => box(8 + i * 38, 55, 34, 16, i % 2 === 0 ? `t${i / 2}` : '·', null, false)));

    if (kind === 'tiling') return h('svg', { viewBox: '0 0 320 68', 'aria-hidden': 'true' },
      ...Array.from({ length: 16 }, (_, k) => {
        const r = Math.floor(k / 4), c = k % 4, hi = r < 2 && c < 2;
        return h('rect', { x: 18 + c * 22, y: 8 + r * 13, width: 19, height: 10, rx: 2, fill: hi ? 'var(--panel-2)' : 'var(--panel)', stroke: hi ? 'var(--good)' : 'var(--line-2)', 'stroke-width': hi ? 1.4 : 1 });
      }),
      arr(116, 34, 146, 34, true),
      txt(156, 26, 'Small tile stays in', 'var(--ink)', 'start', 11),
      txt(156, 42, 'cache / shared mem', 'var(--good)', 'start', 11),
      txt(156, 56, 'while reused many times', 'var(--ink-3)', 'start', 10));

    if (kind === 'barrier') return h('svg', { viewBox: '0 0 320 70', 'aria-hidden': 'true' },
      ...[14, 28, 42, 56].map((y, i) => h('g', {}, txt(8, y + 3, `t${i}`, 'var(--ink-3)'), arr(28, y, 144, y), arr(168, y, 304, y, true))),
      h('line', { x1: 156, y1: 6, x2: 156, y2: 64, stroke: 'var(--good)', 'stroke-width': 2 }),
      txt(156, 69, '__syncthreads()', 'var(--good)', 'middle'));

    if (kind === 'bounds') return h('svg', { viewBox: '0 0 320 64', 'aria-hidden': 'true' },
      arr(18, 28, 302, 28),
      h('rect', { x: 74, y: 18, width: 120, height: 20, rx: 4, fill: 'var(--panel-2)', stroke: 'var(--good)', 'stroke-width': 1.5 }),
      txt(134, 32, '[ 0 .. 7 ]', 'var(--good)', 'middle', 11),
      h('line', { x1: 222, y1: 14, x2: 222, y2: 42, stroke: 'var(--ink-2)', 'stroke-width': 1.5 }),
      txt(222, 54, '8', 'var(--ink)', 'middle', 10),
      txt(134, 54, 'mod %x 8 is provably < 8', 'var(--ink-3)', 'middle', 10));
    return null;
  }

  async function terms() {
    const main = document.querySelector('main');
    if (!main || document.body.classList.contains('home') || /\/resources\/glossary(\.html)?$/.test(location.pathname.replace(/\\/g, '/'))) return;
    let dict;
    try { dict = await fetch(ROOT() + 'data/glossary.json').then(r => (r.ok ? r.json() : null)); } catch { return; }
    if (!dict) return;

    const lookup = new Map(), phrases = [];
    for (const [id, entry] of Object.entries(dict)) {
      if (!entry.m) continue;
      for (const p of entry.m) { lookup.set(p.toLowerCase(), id); phrases.push(p); }
    }
    phrases.sort((a, b) => b.length - a.length);
    const escRe = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const rx = phrases.length ? new RegExp(`(?<![A-Za-z0-9_])(${phrases.map(escRe).join('|')})(?![A-Za-z0-9_])`, 'gi') : null;

    const seen = new Set();
    const skipSel = 'code, pre, a, button, h1, h2, h3, h4, h5, h6, script, style, svg, textarea, .quiz, .exercise, .fig, .eyebrow, .lesson-meta, .term';
    const blocks = main.querySelectorAll('.prose p, .prose li, main > p.lede, main > p.prose, .note p, .trap p, .key p');

    if (rx) {
      for (const blk of blocks) {
        if (blk.closest(skipSel)) continue;
        const walker = document.createTreeWalker(blk, NodeFilter.SHOW_TEXT);
        const nodes = [];
        for (let n = walker.nextNode(); n; n = walker.nextNode()) {
          if (!n.nodeValue.trim() || (n.parentElement && n.parentElement.closest(skipSel))) continue;
          nodes.push(n);
        }
        for (const tn of nodes) {
          const txt = tn.nodeValue;
          rx.lastIndex = 0;
          let m, last = 0, frag = null;
          while ((m = rx.exec(txt)) !== null) {
            const id = lookup.get(m[1].toLowerCase());
            if (!id || seen.has(id)) continue;
            seen.add(id);
            if (!frag) frag = document.createDocumentFragment();
            if (m.index > last) frag.append(document.createTextNode(txt.slice(last, m.index)));
            frag.append(h('button', { type: 'button', class: 'term', 'data-term': id, 'aria-haspopup': 'dialog', text: m[1] }));
            last = m.index + m[0].length;
          }
          if (frag) {
            if (last < txt.length) frag.append(document.createTextNode(txt.slice(last)));
            tn.replaceWith(frag);
          }
        }
      }
    }

    const isSheet = () => TOUCH || window.innerWidth <= 720;
    let pop = null, scrim = null, activeBtn = null, pinned = false, openT = 0, closeT = 0;

    function closePop(restoreFocus) {
      clearTimeout(openT); clearTimeout(closeT);
      if (activeBtn) { activeBtn.classList.remove('open'); if (restoreFocus) activeBtn.focus(); activeBtn = null; }
      if (pop) { pop.remove(); pop = null; }
      if (scrim) { scrim.remove(); scrim = null; }
      pinned = false;
    }

    function positionPop(btn) {
      if (!pop || isSheet()) return;
      const r = btn.getBoundingClientRect(), pr = pop.getBoundingClientRect();
      const pad = 12, gap = 8;
      let left = r.left + r.width / 2 - pr.width / 2;
      left = Math.max(pad, Math.min(window.innerWidth - pr.width - pad, left));
      let top = r.top - pr.height - gap;
      if (top < pad + 52) top = r.bottom + gap;
      if (top + pr.height > window.innerHeight - pad) top = Math.max(pad + 52, window.innerHeight - pr.height - pad);
      pop.style.left = Math.round(left) + 'px';
      pop.style.top = Math.round(top) + 'px';
    }

    function openPop(btn, pin) {
      const id = btn.dataset.term, entry = dict[id];
      if (!entry) return;
      clearTimeout(openT); clearTimeout(closeT);
      if (activeBtn === btn && pop) { pinned = pinned || pin; return; }
      closePop(false);
      activeBtn = btn; pinned = pin;
      btn.classList.add('open');

      const sheet = isSheet();
      const closeBtn = h('button', { type: 'button', class: 'term-close', 'aria-label': 'Close definition', text: '×', onclick: () => closePop(true) });
      const bodyKids = [h('p', { class: 'term-def', text: entry.d })];
      if (entry.v) { const svg = termViz(entry.v); if (svg) bodyKids.push(h('div', { class: 'term-viz' }, svg)); }
      if (entry.e) bodyKids.push(h('pre', { class: 'term-ex' }, h('code', { text: entry.e })));

      const footKids = [];
      if (entry.w && entry.w.length) {
        const [href, label] = entry.w[0];
        footKids.push(h('span', {}, 'Lesson: ', h('a', { href: ROOT() + href, text: label })));
      }
      footKids.push(h('a', { href: ROOT() + 'resources/glossary.html#t-' + id, text: 'Glossary →' }));

      pop = h('div', { class: 'term-pop' + (sheet ? ' sheet' : ''), role: 'dialog', 'aria-label': entry.t },
        h('div', { class: 'term-head' }, h('span', { class: 'term-title', text: entry.t }), closeBtn),
        h('div', { class: 'term-body' }, ...bodyKids),
        h('div', { class: 'term-foot' }, ...footKids));

      if (!sheet) {
        pop.addEventListener('pointerenter', () => clearTimeout(closeT));
        pop.addEventListener('pointerleave', () => { if (!pinned) closeT = setTimeout(() => closePop(false), 180); });
      } else {
        scrim = h('div', { class: 'term-scrim', onclick: () => closePop(false) });
        document.body.append(scrim);
      }
      document.body.append(pop);
      positionPop(btn);
    }

    main.addEventListener('pointerover', e => {
      if (isSheet() || e.pointerType !== 'mouse') return;
      const btn = e.target.closest('button.term');
      if (!btn) return;
      clearTimeout(closeT);
      if (activeBtn === btn) return;
      clearTimeout(openT);
      openT = setTimeout(() => openPop(btn, false), 90);
    });
    main.addEventListener('pointerout', e => {
      if (isSheet() || e.pointerType !== 'mouse') return;
      const btn = e.target.closest('button.term');
      if (!btn || pinned) return;
      clearTimeout(openT);
      closeT = setTimeout(() => closePop(false), 180);
    });
    main.addEventListener('click', e => {
      const btn = e.target.closest('button.term');
      if (!btn) return;
      e.preventDefault();
      if (activeBtn === btn && pinned) closePop(false);
      else openPop(btn, true);
    });
    document.addEventListener('click', e => {
      if (!pop || e.target.closest('.term-pop') || e.target.closest('button.term')) return;
      closePop(false);
    });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && pop) closePop(true); });
    window.addEventListener('scroll', () => { if (pop && activeBtn && !isSheet()) positionPop(activeBtn); }, { passive: true });
    window.addEventListener('resize', () => { if (pop && activeBtn) { if (isSheet()) pop.classList.add('sheet'); else { pop.classList.remove('sheet'); positionPop(activeBtn); } } });
  }

  document.addEventListener('DOMContentLoaded', () => { frame(); quizzes(); exercises(); terms(); siteKeys(); });
  const pathNext = () => { const pid = pathId(); return pid ? nextUp(pid) : null; };
  return { h, graph, parseUir, stepper, trace, code, NAV, quizzes, quizId, store, dueQuizzes, nextReview, pathNext, forget, track, today, lessonDone, REVIEW_MAX };
})();
