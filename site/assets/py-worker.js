// py-worker.js: runs Python and .uir exercises in the browser via Pyodide (WebAssembly Python).
// Used on sharpterminal.com when the local runner (tools/serve.py) isn't running, so every
// Python and .uir exercise runs live with zero install.
let pyodide = null;
let uircLoaded = false;

async function ensurePyodide() {
  if (pyodide) return pyodide;
  self.postMessage({ type: 'status', text: 'Starting Python in your browser (a few seconds, once)…' });
  importScripts('https://cdn.jsdelivr.net/pyodide/v0.27.5/full/pyodide.js');
  pyodide = await loadPyodide({ indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.27.5/full/' });
  return pyodide;
}

async function ensureUirc(uircUrl) {
  const py = await ensurePyodide();
  if (uircLoaded) return py;
  self.postMessage({ type: 'status', text: 'Loading the .uir validator…' });
  const resp = await fetch(uircUrl);
  if (!resp.ok) throw new Error('Could not load uirc.py (' + resp.status + ')');
  const src = await resp.text();
  py.FS.writeFile('/uirc.py', src);
  await py.runPythonAsync(`
import sys, importlib.util
if '/' not in sys.path: sys.path.insert(0, '/')
import uirc as _O
`);
  uircLoaded = true;
  return py;
}

const PY_GRADER = `
import io, re, sys, json, traceback, contextlib

def _clip(s, cap=4000):
    return s if len(s) <= cap else s[:cap] + f"\\n... ({len(s) - cap} more chars)"

def _label(ex, t):
    if 'data' in t:
        return '\\n'.join(f"buffer slot {k} starts as [{' '.join(map(str, v))}]" for k, v in t['data'].items()) + f"\\nfinal contents of slot {t.get('out', ex.get('out_slot', 0))}"
    if 'args' in t:
        return f"%out({', '.join(map(str, t['args']))})"
    return t.get('expr', '')

def _grade_python(ex, code, tests, everything):
    buf = io.StringIO()
    ns = {'__name__': '__main__'}
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(code, 'solution.py', 'exec'), ns)
    except Exception:
        tb = traceback.format_exc()
        return {'ok': False, 'error': _clip(tb), 'stdout': _clip(buf.getvalue().strip())}
    try:
        show = eval(ex.get('show', 'str'), ns)
    except Exception:
        tb = traceback.format_exc()
        return {'ok': False, 'error': _clip(tb) + "\\n(The error is in the test harness: keep the function name and signature the starter code gives you.)", 'stdout': _clip(buf.getvalue().strip())}
    got = []
    for t in tests:
        try:
            with contextlib.redirect_stdout(buf):
                val = eval(t['expr'], ns)
            got.append(str(show(val)))
        except Exception as e:
            got.append('exception ' + type(e).__name__ + (': ' + str(e) if str(e) else ''))
    return _finish(ex, tests, got, everything, _clip(buf.getvalue().strip()))

def _fmt(v, dt):
    if isinstance(v, tuple): return '[' + ' '.join(_fmt(x, dt) for x in v) + ']'
    return _O.lit(_O.const(v, dt))

def _with_data(code, data):
    out = []
    for line in code.split('\\n'):
        m = re.search(r"\\bbuffer\\b.*\\bslot=([0-9]+)", line.split('#', 1)[0])
        if m and m.group(1) in data:
            vals = '[' + ' '.join(str(v).lower() if isinstance(v, bool) else str(v) for v in data[m.group(1)]) + ']'
            line = re.sub(r"\\b(buffer[ \\t]+[0-9]+)(?:[ \\t]+\\[[^\\]]*\\])?", lambda g: g.group(1) + ' ' + vals, line.split('#', 1)[0], count=1).rstrip()
        out.append(line)
    return '\\n'.join(out)

def _grade_uir(ex, code, tests, everything):
    m = re.match(r"w([0-9]+)-", ex['id'])
    _O.WEEK = int(m.group(1)) if m and m.group(1) != '0' else 10
    if ex.get('mode') == 'buffers':
        try: _O.parse(code)
        except _O.UIRError as e: return {'ok': False, 'error': f"invalid .uir: {e}", 'stdout': ''}
        stripped = '\\n'.join(l.split('#', 1)[0] for l in code.split('\\n'))
        for pat, why in ex.get('require', []):
            if not re.search(pat, stripped): return {'ok': False, 'error': why, 'stdout': ''}
        got = []
        for t in tests:
            try:
                fb = _O.final_buffers(_O.parse(_with_data(code, {str(k): v for k, v in t.get('data', {}).items()}))[0])
                slot = t.get('out', ex.get('out_slot', 0))
                if slot not in fb: got.append(f"error: no buffer with slot {slot}"); continue
                dt, vals = fb[slot]
                got.append(_fmt(tuple(vals), dt))
            except _O.UIRError as e: got.append(f"error: {e}")
        return _finish(ex, tests, got, everything, '')
    try:
        names = _O.parse(code)[0]
        if 'out' not in names: return {'ok': False, 'error': "your program must define %out", 'stdout': ''}
        out = names['out']
        if ex.get('max_ops') is not None and (n := _O.count_ops(out)) > ex['max_ops']:
            return {'ok': False, 'error': f"%out uses {n} ops; this exercise allows at most {ex['max_ops']}", 'stdout': ''}
    except _O.UIRError as e:
        return {'ok': False, 'error': f"invalid .uir: {e}", 'stdout': ''}
    got = []
    for t in tests:
        try:
            args = [_O.literal(str(a).lower() if isinstance(a, bool) else str(a)) for a in t['args']]
            got.append(_fmt(_O.evaluate(_O.build('call', [out] + args, {}), None), out.dtype))
        except _O.UIRError as e: got.append(f"error: {e}")
    return _finish(ex, tests, got, everything, '')

def _finish(ex, tests, got, everything, user):
    results = []
    for t, g in zip(tests, got):
        shown = t.get('sample') or not everything
        results.append({'input': _label(ex, t), 'expect': str(t['expect']), 'got': g,
                        'pass': g.strip() == str(t['expect']).strip(), 'hidden': not shown})
    first_bad = next((r for r in results if not r['pass'] and r['hidden']), None)
    for r in results:
        if r['hidden'] and r is not first_bad:
            r['input'] = r['expect'] = r['got'] = None
    return {'ok': True, 'results': results, 'passed': sum(1 for r in results if r['pass']), 'total': len(results), 'stdout': user}

def _run_job(payload_json):
    job = json.loads(payload_json)
    ex, code, submit = job['ex'], job['code'], bool(job['submit'])
    tests = ex['tests'] if submit else [t for t in ex['tests'] if t.get('sample')]
    res = _grade_uir(ex, code, tests, submit) if ex['lang'] == 'uir' else _grade_python(ex, code, tests, submit)
    return json.dumps(res)
`;

let graderInstalled = false;

self.onmessage = async (ev) => {
  const { id, ex, code, submit, uircUrl } = ev.data;
  try {
    const py = ex.lang === 'uir' ? await ensureUirc(uircUrl) : await ensurePyodide();
    if (!graderInstalled) {
      await py.runPythonAsync(PY_GRADER);
      graderInstalled = true;
    }
    py.globals.set('_payload_json', JSON.stringify({ ex, code, submit }));
    const resJson = await py.runPythonAsync('_run_job(_payload_json)');
    self.postMessage({ type: 'result', id, res: JSON.parse(resJson) });
  } catch (err) {
    self.postMessage({ type: 'error', id, message: String(err && err.message ? err.message : err) });
  }
};
