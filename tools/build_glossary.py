#!/usr/bin/env python3
"""Build site/data/glossary.json from site/resources/glossary.html.

Run after editing site/resources/glossary.html:
  python tools/build_glossary.py
"""
import html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
GLOSSARY = ROOT / 'site' / 'resources' / 'glossary.html'
OUT = ROOT / 'site' / 'data' / 'glossary.json'

VIZ_MAP = {
  'uop': 'uop',
  'tuple': 'tuple',
  'dag': 'dag',
  'graph': 'dag',
  'hash-consing': 'hash-consing',
  'memoization': 'memoization',
  'toposort': 'toposort',
  'fixpoint': 'fixpoint',
  'cache-line': 'cache-line',
  'coalescing': 'coalescing',
  'tiling': 'tiling',
  'barrier': 'barrier',
  'bounds-analysis': 'bounds',
}

AUTO_MATCH = {
  'uop': ['UOp', 'UOps'],
  'tuple': ['tuple', 'tuples'],
  'dag': ['DAG', 'DAGs'],
  'graph': ['graph', 'graphs'],
  'hash-consing': ['hash consing', 'hash-consing', 'hash-consed', 'hash cons'],
  'memoization': ['memoization', 'memo table', 'memo tables'],
  'toposort': ['toposort', 'topological order'],
  'fixpoint': ['fixpoint', 'fixed point'],
  'canonical-form': ['canonical form', 'canonicalization', 'canonical'],
  'commutative': ['commutative'],
  'structural-equality': ['structural equality'],
  'physical-equality': ['physical equality'],
  'identity': ['node identity', 'by identity', 'pointer identity'],
  'literal': ['literal', 'literals'],
  'operand': ['operand', 'operands'],
  'subgraph': ['subgraph', 'subgraphs'],
  'dtype': ['dtype', 'dtypes'],
  'addrspace': ['addrspace'],
  'bounds-analysis': ['bounds analysis'],
  'constant-folding': ['constant folding'],
  'closure-conversion': ['closure conversion'],
  'beta-reduction': ['beta reduction'],
  'array-decay': ['array decay'],
  'arithmetic-intensity': ['arithmetic intensity'],
  'bank-conflict': ['bank conflict', 'bank conflicts'],
  'bitcast': ['bitcast'],
  'cache-line': ['cache line', 'cache lines'],
  'coalescing': ['coalescing', 'coalesced'],
  'contiguous': ['contiguous'],
  'autodiff': ['autodiff', 'automatic differentiation'],
  'broadcast': ['broadcast', 'broadcasting'],
  'cross-entropy': ['cross-entropy'],
  'dataclass': ['dataclass', 'dataclasses'],
  'dot-product': ['dot product', 'dot products'],
  'elementwise': ['elementwise'],
  'emulator': ['emulator'],
  'eviction': ['eviction', 'evicted'],
  'exhaustiveness-check': ['exhaustiveness check'],
  'false-sharing': ['false sharing'],
  'fission': ['fission'],
  'flash-attention': ['flash attention'],
  'flat-index': ['flat index'],
  'flop': ['FLOP', 'FLOPs'],
  'fused-multiply-add-fma': ['fused multiply-add', 'FMA'],
  'gemm': ['GEMM', 'GEMMs'],
  'gradient-descent': ['gradient descent'],
  'hardware-prefetcher': ['hardware prefetcher', 'prefetcher'],
  'hash-table': ['hash table', 'hash tables'],
  'hex-float': ['hex float', 'hex floats'],
  'hoisting': ['hoisting'],
  'horner-s-rule': ["Horner's rule"],
  'im2col': ['im2col'],
  'implicit-gemm': ['implicit GEMM'],
  'l2-cache': ['L2 cache'],
  'lambda-calculus': ['lambda calculus'],
  'lexer': ['lexer'],
  'linearize': ['linearize', 'linearizing'],
  'little-endian': ['little-endian'],
  'load-placement': ['load placement'],
  'local-memory': ['local memory'],
  'logit': ['logit', 'logits'],
  'loop-carried': ['loop-carried'],
  'loop-invariant': ['loop-invariant'],
  'lru': ['LRU'],
  'mantissa': ['mantissa'],
  'materialize': ['materialize', 'materialization', 'materialized'],
  'mixed-radix-rule': ['mixed-radix'],
  'movement-op': ['movement op', 'movement ops'],
  'nan': ['NaN'],
  'negative-zero-0-0': ['negative zero'],
  'newton-s-method': ["Newton's method"],
  'numel': ['numel'],
  'occupancy': ['occupancy'],
  'one-hot': ['one-hot'],
  'online-softmax': ['online softmax'],
  'outlining': ['outlining'],
  'overflow': ['overflow'],
  'parser': ['parser'],
  'pattern-match': ['pattern match', 'pattern matching'],
  'per-thread-memory': ['per-thread memory'],
  'permute': ['permute'],
  'pointer': ['pointer', 'pointers'],
  'post-order': ['post-order', 'postorder'],
  'quantization': ['quantization'],
  'rangeify': ['rangeify'],
  'recip': ['recip'],
  'register': ['register', 'registers'],
  'register-spill': ['register spill', 'register spills'],
  'reshape': ['reshape'],
  'reverse-mode': ['reverse mode', 'reverse-mode'],
  'rewrite-rule': ['rewrite rule', 'rewrite rules'],
  'roofline': ['roofline'],
  'row-major': ['row-major'],
  'sanitizer': ['sanitizer'],
  'scalar': ['scalar', 'scalars'],
  'shared-memory': ['shared memory'],
  'simd': ['SIMD'],
  'softmax': ['softmax'],
  'stride': ['stride', 'strided'],
  'subnormal': ['subnormal', 'subnormals'],
  'substitution': ['substitution'],
  'taylor-series': ['Taylor series'],
  'tensor': ['tensor', 'tensors'],
  'tensor-core': ['tensor core', 'tensor cores'],
  'tile-major': ['tile-major'],
  'tiling': ['tiling'],
  'transpose': ['transpose'],
  'trip-count': ['trip count'],
  'truncation': ['truncation'],
  'two-s-complement': ["two's complement"],
  'ulp': ['ulp', 'ULP'],
  'undefined-behavior-ub': ['undefined behavior'],
  'unflatten': ['unflatten'],
  'unroll': ['unroll', 'unrolling'],
  'upcast': ['upcast', 'upcasting'],
  'warp': ['warp', 'warps'],
  'wmma': ['wmma'],
  'wrap-around': ['wrap around', 'wraparound'],
  'zero-padding': ['zero padding'],
  'accumulator': ['accumulator', 'accumulators'],
  'barrier': ['barrier', 'barriers'],
  'closure': ['closure', 'closures'],
  'convolution': ['convolution', 'convolutions'],
  'gradient': ['gradient', 'gradients'],
  'interpreter': ['interpreter'],
  'ir': ['IR', 'IRs'],
  'buffer': ['buffer', 'buffers'],
}

def strip_tags(s):
  return ' '.join(html.unescape(re.sub(r'<[^>]+>', '', s)).split())

def main():
  src = GLOSSARY.read_text(encoding='utf-8')
  blocks = re.findall(r'<div class="g-term" id="t-([^"]+)">(.*?)</div>', src, re.S)
  terms = {}
  for tid, body in blocks:
    h3 = re.search(r'<h3>(.*?)</h3>', body, re.S)
    ps = re.findall(r'<p(?:\s+class="([^"]*)")?>(.*?)</p>', body, re.S)
    if not h3 or not ps: continue
    name = strip_tags(h3.group(1))
    defn, ex, refs = '', '', []
    for cls, inner in ps:
      if cls == 'g-ex':
        ex = strip_tags(inner)
      elif cls == 'g-where':
        for href, label in re.findall(r'<a href="\.\./([^"]+)">(.*?)</a>', inner):
          refs.append([href, strip_tags(label)])
      elif not cls and not defn:
        defn = strip_tags(inner)
    entry = {'t': name, 'd': defn}
    if ex: entry['e'] = ex
    if refs: entry['w'] = refs[:2]
    if tid in VIZ_MAP: entry['v'] = VIZ_MAP[tid]
    if tid in AUTO_MATCH: entry['m'] = AUTO_MATCH[tid]
    terms[tid] = entry

  OUT.parent.mkdir(parents=True, exist_ok=True)
  OUT.write_text(json.dumps(terms, ensure_ascii=False, separators=(',', ':')), encoding='utf-8', newline='\n')
  auto_n = sum(1 for v in terms.values() if 'm' in v)
  viz_n = sum(1 for v in terms.values() if 'v' in v)
  print(f'wrote {OUT.relative_to(ROOT)}: {len(terms)} terms ({auto_n} auto-matched, {viz_n} with diagrams)')

if __name__ == '__main__':
  main()
