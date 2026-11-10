#!/usr/bin/env python3
"""MNIST for week 6.

  python tools/mnist.py program [--steps 50] [--batch 100] [--lr 1.0] [--base URL]   # print the training program
  python tools/mnist.py data RAW_DIR                                                  # maintainers: rebuild the data files

The program trains a softmax regression (one 784x10 layer) with minibatch gradient descent, then counts
how many of 1000 test digits it gets right and stores that count in slot 4. Every step is written out:
week 6 has no loops around whole tensors, so step k reads batch k and the weights step k-1 stored.

The data files are a fixed slice of the official MNIST set (yann.lecun.com, mirrored by Google at
storage.googleapis.com/cvdf-datasets/mnist): the first 5000 training and first 1000 test images.
Pixels are f32 in [0, 1] (byte / 255), labels are i32, all little-endian, row-major.
"""
import sys, os, gzip, struct, hashlib, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'tests', 'week6', 'render', 'data')
FILES = {   # name: (source file, count, dtype)
  'mnist-train-images.f32': ('train-images-idx3-ubyte.gz', 5000, 'f32'),
  'mnist-train-labels.i32': ('train-labels-idx1-ubyte.gz', 5000, 'i32'),
  'mnist-test-images.f32': ('t10k-images-idx3-ubyte.gz', 1000, 'f32'),
  'mnist-test-labels.i32': ('t10k-labels-idx1-ubyte.gz', 1000, 'i32'),
}
RAW_SHA = {   # the published MNIST archives
  'train-images-idx3-ubyte.gz': '440fcabf73cc546fa21475e81ea370265605f56be210a4024d2ca8f203523609',
  'train-labels-idx1-ubyte.gz': '3552534a0a558bbed6aed32b30c495cca23d567ec52cac8be1a0730e8010255c',
  't10k-images-idx3-ubyte.gz': '8d422c7b0a1c1c79245a5bcf07fe86e33eeafee792b84584aec276f5a2dbc4e6',
  't10k-labels-idx1-ubyte.gz': 'f7ae60f92e00ec6debd23a6088c31dbd2371eca3ffa0defaefb259924204aec6',
}

def convert(raw):
  os.makedirs(DATA, exist_ok=True)
  for name, (src, n, dt) in FILES.items():
    b = open(os.path.join(raw, src), 'rb').read()
    if hashlib.sha256(b).hexdigest() != RAW_SHA[src]: sys.exit(f"{src}: sha256 doesn't match the published MNIST file")
    b = gzip.decompress(b)
    if dt == 'f32':
      magic, count, rows, cols = struct.unpack('>4i', b[:16]); assert magic == 2051 and (rows, cols) == (28, 28)
      px = b[16:16 + n * 784]
      out = struct.pack(f'<{n * 784}f', *[p / 255 for p in px])
    else:
      magic, count = struct.unpack('>2i', b[:8]); assert magic == 2049
      out = struct.pack(f'<{n}i', *b[8:8 + n])
    open(os.path.join(DATA, name), 'wb').write(out)
    print(f"{name}: {len(out)} bytes, sha256 {hashlib.sha256(out).hexdigest()}")

def sha(name): return hashlib.sha256(open(os.path.join(DATA, name), 'rb').read()).hexdigest()

def program(steps, batch, lr, base):
  N, T, P, C = 5000, 1000, 784, 10
  assert steps * batch <= N, "not enough training images for that many steps"
  url = lambda f: (base.rstrip('/') + '/' + f) if base else f'data/{f}'
  L = [f"# render check: slot 4 >= 850",
       f"# time: 120",
       f"# max_bytes: {30000 + 20000 * steps}",
       f"# softmax regression on MNIST: {steps} steps of {batch} images, learning rate {lr}, then 1000 test digits",
       f"%xs = buffer {N * P} dtype=f32 slot=0 url={url('mnist-train-images.f32')} sha256={sha('mnist-train-images.f32')}",
       f"%ys = buffer {N} dtype=i32 slot=1 url={url('mnist-train-labels.i32')} sha256={sha('mnist-train-labels.i32')}",
       f"%xt = buffer {T * P} dtype=f32 slot=2 url={url('mnist-test-images.f32')} sha256={sha('mnist-test-images.f32')}",
       f"%yt = buffer {T} dtype=i32 slot=3 url={url('mnist-test-labels.i32')} sha256={sha('mnist-test-labels.i32')}",
       f"%ok = buffer 1 dtype=i32 slot=4",
       f"%w = buffer {P * C} dtype=f32 slot=5             # the weights, starting at zero",
       f"%cls = buffer {C} dtype=i32 slot=6 data=[{' '.join(map(str, range(C)))}]",
       f"%classes = load %cls",
       "",
       "# one-hot labels: onehot[b][c] is 1.0 where label b is class c",
       "# logits are staged: computed once per step, and so is their gradient"]
  def onehot(lab, n, v):
    return [f"%{v}l = reshape {lab} shape=[{n} 1]",
            f"%{v}e = expand %{v}l shape=[{n} {C}]",
            f"%{v}c = reshape %classes shape=[1 {C}]",
            f"%{v}k = expand %{v}c shape=[{n} {C}]",
            f"%{v}q = cmpeq %{v}e %{v}k",
            f"%{v} = cast %{v}q dtype=f32"]
  wv = '%w'
  for k in range(steps):
    s = f"s{k}_"
    L += [f"# step {k}",
          f"%{s}xv = shrink %xs {k * batch * P} shape=[{batch * P}]",
          f"%{s}xl = load %{s}xv",
          f"%{s}x = reshape %{s}xl shape=[{batch} {P}]",
          f"%{s}yv = shrink %ys {k * batch} shape=[{batch}]",
          f"%{s}yl = load %{s}yv"]
    L += onehot(f"%{s}yl", batch, f"{s}oh")
    L += [f"%{s}wl = load {wv}",
          f"%{s}W = reshape %{s}wl shape=[{P} {C}]",
          f"%{s}z0 = matmul %{s}x %{s}W",
          f"%{s}z = stage %{s}z0",
          # log-softmax over the class axis: put classes first so reduce pops them
          f"%{s}zt = permute %{s}z order=[1 0]",
          f"%{s}m = reduce %{s}zt op=max",
          f"%{s}md = detach %{s}m",
          f"%{s}mr = reshape %{s}md shape=[{batch} 1]",
          f"%{s}me = expand %{s}mr shape=[{batch} {C}]",
          f"%{s}zs = sub %{s}z %{s}me",
          f"%{s}e = exp %{s}zs",
          f"%{s}et = permute %{s}e order=[1 0]",
          f"%{s}se = reduce %{s}et op=add",
          f"%{s}ls = log %{s}se",
          f"%{s}lr = reshape %{s}ls shape=[{batch} 1]",
          f"%{s}le = expand %{s}lr shape=[{batch} {C}]",
          f"%{s}lp = sub %{s}zs %{s}le",
          f"%{s}pick = mul %{s}lp %{s}oh",
          f"%{s}pf = reshape %{s}pick shape=[{batch * C}]",
          f"%{s}tot = reduce %{s}pf op=add",
          f"%{s}loss = mul %{s}tot {-1.0 / batch!r}",
          f"%{s}g = gradient %{s}loss %{s}W",
          f"%{s}lrx = expand {float(lr)!r} shape=[{P} {C}]",
          f"%{s}d = mul %{s}g %{s}lrx",
          f"%{s}W1 = sub %{s}W %{s}d",
          f"%{s}wf = reshape %{s}W1 shape=[{P * C}]",
          f"%{s}st = store {wv} %{s}wf",
          f"%{s}w = after {wv} %{s}st"]
    wv = f"%{s}w"
  L += ["", "# test: a digit counts as right when its label's logit is the largest",
        f"%tl = load %xt",
        f"%tx = reshape %tl shape=[{T} {P}]",
        f"%twl = load {wv}",
        f"%tW = reshape %twl shape=[{P} {C}]",
        f"%tz0 = matmul %tx %tW",
        f"%tz = stage %tz0",
        f"%tzt = permute %tz order=[1 0]",
        f"%tm = reduce %tzt op=max",
        f"%tyl = load %yt"]
  L += onehot("%tyl", T, "toh")
  L += [f"%tp = mul %tz %toh",
        f"%tpt = permute %tp order=[1 0]",
        f"%tpick = reduce %tpt op=add          # the label's logit",
        f"%tlow = cmplt %tpick %tm",
        f"%tyes = expand true shape=[{T}]",
        f"%thit = xor %tlow %tyes",
        f"%tn = cast %thit dtype=i32",
        f"%tc = reduce %tn op=add",
        f"%okv = shrink %ok 0 shape=[]",
        f"%okst = store %okv %tc",
        f"%ok1 = after %ok %okst"]
  return '\n'.join(l for l in L if l) + '\n'

if __name__ == '__main__':
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  sub = ap.add_subparsers(dest='cmd', required=True)
  p = sub.add_parser('program'); p.add_argument('--steps', type=int, default=50); p.add_argument('--batch', type=int, default=100)
  p.add_argument('--lr', type=float, default=1.0); p.add_argument('--base', default='')
  d = sub.add_parser('data'); d.add_argument('raw')
  a = ap.parse_args()
  if a.cmd == 'data': convert(a.raw)
  else: sys.stdout.write(program(a.steps, a.batch, a.lr, a.base))
