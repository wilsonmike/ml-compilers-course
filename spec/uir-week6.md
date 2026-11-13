# .uir, week 6: math, autodiff and data (provisional)

Week 6 makes your compiler able to train a model. It adds four math functions (`exp2`, `log2`,
`sqrt`, `sin`) built from adds and multiplies, a set of **sugar** ops that expand into core ops,
**`gradient`** and **`detach`** for automatic differentiation, and buffers read from files with
`url=` and `sha256=`. The lab trains a digit classifier on MNIST. Everything in weeks 1 to 5 still
holds. The syllabus names GRADIENT, DETACH, `url=`, `sha256=`, syntactic sugar, MNIST training and the
Taylor expansions for SIN, LOG2, EXP2 and SQRT; the rest is our design, provisional until the official
format is published.

Op names may now contain digits after the first letter (`exp2`). The grammar is otherwise unchanged.

## 1. Two new core ops

| op | attributes | operands | result | notes |
|---|---|---|---|---|
| `bitcast x` | `dtype` (`i32` or `f32`) | an i32 or f32 value | same shape, the new dtype | The same 32 bits, read as the other type. `bitcast 1.0 dtype=i32` is `1065353216`. Any NaN gives `2143289344` (`0x7fc00000`), so the result doesn't depend on which NaN you had. |
| `detach x` | none | any value | same as `x` | The same value. Gradients don't flow through it (section 4). |

## 2. Math ops

`exp2 x`, `log2 x`, `sqrt x` and `sin x` take an f32 value of any shape and work elementwise. Each is
**defined** by the exact core-op program below, applied to every element. Your results must match
it bit for bit, so implement exactly these steps (your own polynomial, however accurate, will differ in
the last bit). The definitions are accurate: `exp2`, `log2` and `sqrt` are within about 1.5 units in the
last place of the true value, and `sin` is within 3e-7 of it for `|x| ≤ 10000` (beyond that its result
is still a number in `[-1, 1]`, just not a meaningful one).

Each body below is a call body: `%x` is the argument and `%r` the result. `floor` is sugar
(section 3). The special values, which fall out of the definitions:

| x | `exp2` | `log2` | `sqrt` | `sin` |
|---|---|---|---|---|
| `nan` | nan | nan | nan | nan |
| `inf` | inf | inf | inf | nan |
| `-inf` | 0.0 | nan | nan | nan |
| `0.0` / `-0.0` | 1.0 | -inf | 0.0 / -0.0 | 0.0 / -0.0 |
| negative | (finite) | nan | nan | (finite) |

### exp2

Split `x` into a nearest integer `n` and a remainder `f` in `[-0.5, 0.5]`. Then `2^x = 2^f · 2^n`:
`2^f` comes from its Taylor series, and `2^n` is built directly from its bits. The bit pattern
`(n + 127) · 2^23` only covers n in [-126, 127], and n runs from -150 to 128, so `2^n` is two factors,
`2^h · 2^k`, each in [-75, 64]: subnormal results and results just below `2^128` both come out right.

```
%x   = param 0 dtype=f32
%lo  = cmplt %x inf
%hi  = cmplt -inf %x
%h1  = where %hi false true
%nan = where %lo false %h1             # x is nan
%x0  = where %nan 0.0 %x
%c1  = cmplt 128.0 %x0
%x1  = where %c1 128.0 %x0             # 2^128 is already inf in f32
%c2  = cmplt %x1 -150.0
%xc  = where %c2 -150.0 %x1            # 2^-150 already rounds to 0
%xh  = add %xc 0.5
%n   = floor %xh                       # the nearest integer
%nn  = mul %n -1.0
%f   = add %xc %nn                     # in [-0.5, 0.5]
%a7  = mul 1.5252734e-05 %f            # 2^f, Horner's rule: c_k = ln(2)^k / k!, k = 7 down to 0
%b6  = add %a7 0.0001540353
%a6  = mul %b6 %f
%b5  = add %a6 0.0013333558
%a5  = mul %b5 %f
%b4  = add %a5 0.009618129
%a4  = mul %b4 %f
%b3  = add %a4 0.05550411
%a3  = mul %b3 %f
%b2  = add %a3 0.2402265
%a2  = mul %b2 %f
%b1  = add %a2 0.6931472
%a1  = mul %b1 %f
%p   = add %a1 1.0
%ni  = cast %n dtype=i32
%h   = div %ni 2
%hn  = mul %h -1
%k   = add %ni %hn                     # h + k = n, both in [-75, 64]
%eh  = add %h 127
%bh  = mul %eh 8388608
%sh  = bitcast %bh dtype=f32           # 2^h: exponent field h + 127, mantissa 0
%ek  = add %k 127
%bk  = mul %ek 8388608
%sk  = bitcast %bk dtype=f32           # 2^k
%ps  = mul %p %sh
%pk  = mul %ps %sk
%r   = where %nan %x %pk
```

### log2

Write `x = m · 2^e` with `m` in `[0.707, 1.414]`, read straight from the bits. Then
`log2 x = e + log2 m`, and with `s = (m - 1) / (m + 1)`, `log2 m = (2 / ln 2)(s + s³/3 + s⁵/5 + ...)`.
`|s| ≤ 0.172`, so five terms are plenty. Subnormal inputs are scaled up by `2^23` first.

```
%x   = param 0 dtype=f32
%p0  = cmplt 0.0 %x
%fin = cmplt %x inf
%ok  = where %p0 %fin false            # 0 < x < inf
%xs  = where %ok %x 1.0
%sub = cmplt %xs 1.1754944e-38         # subnormal
%xu  = mul %xs 8388608.0
%xn  = where %sub %xu %xs
%b   = bitcast %xn dtype=i32
%bd  = div %b 8388608
%e   = add %bd -127                    # the exponent field
%bm  = mod %b 8388608
%bo  = add %bm 1065353216              # the mantissa with exponent 0
%m   = bitcast %bo dtype=f32           # in [1, 2)
%big = cmplt 1.4142135 %m
%mh  = mul %m 0.5
%m2  = where %big %mh %m               # in [0.707, 1.414]
%bi  = cast %big dtype=i32
%e1  = add %e %bi
%ef  = cast %e1 dtype=f32
%adj = where %sub -23.0 0.0
%e2  = add %ef %adj
%mm  = add %m2 -1.0
%mp  = add %m2 1.0
%ri  = recip %mp
%s   = mul %mm %ri
%z   = mul %s %s
%a9  = mul 0.3205989 %z                # c_k = 2 / (k ln 2), k = 9, 7, 5, 3, 1
%b7  = add %a9 0.41219857
%a7  = mul %b7 %z
%b5  = add %a7 0.57707804
%a5  = mul %b5 %z
%b3  = add %a5 0.9617967
%a3  = mul %b3 %z
%q   = add %a3 2.88539
%sq  = mul %s %q
%y   = add %e2 %sq
%neg = cmplt %x 0.0
%bad = where %neg nan -inf
%y1  = where %p0 %y %bad
%r   = where %fin %y1 %x
```

### sqrt

A first guess from `exp2` and `log2`, then one Newton step, `y = (y + x / y) / 2`.

```
%x   = param 0 dtype=f32
%p0  = cmplt 0.0 %x
%fin = cmplt %x inf
%ok  = where %p0 %fin false
%xs  = where %ok %x 1.0
%l   = log2 %xs
%lh  = mul %l 0.5
%y0  = exp2 %lh
%ry  = recip %y0
%xy  = mul %xs %ry
%sm  = add %y0 %xy
%y   = mul %sm 0.5
%neg = cmplt %x 0.0
%bad = where %neg nan %x               # sqrt(0.0) is 0.0, sqrt(-0.0) is -0.0
%y1  = where %p0 %y %bad
%r   = where %fin %y1 %x
```

### sin

Subtract the nearest whole number of turns, `k · 2π`, using 2π split into an exactly representable
part and a small correction. Fold the result into `[-π/2, π/2]` with `sin(π - r) = sin r`, then use
the Taylor series up to `r^13`.

```
%x   = param 0 dtype=f32
%nx  = mul %x -1.0
%ax  = max %x %nx
%fin = cmplt %ax inf                   # finite (false for nan)
%xs  = where %fin %x 0.0
%t   = mul %xs 0.15915494              # turns: x / 2pi
%th  = add %t 0.5
%k   = floor %th
%k1  = mul %k -6.28125
%r0  = add %xs %k1
%k2  = mul %k -0.0019353072            # 6.28125 + 0.0019353072 = 2pi
%rd  = add %r0 %k2                     # in about [-pi, pi]
%nr  = mul %rd -1.0
%up  = cmplt 1.5707964 %rd
%fu  = add 3.1415927 %nr               # pi - r
%dn  = cmplt %rd -1.5707964
%fd  = add -3.1415927 %nr              # -pi - r
%w1  = where %dn %fd %rd
%rf  = where %up %fu %w1               # in [-pi/2, pi/2]
%hi  = cmplt 1.5707964 %rf
%mx  = max %rf -1.5707964
%rc  = where %hi 1.5707964 %mx         # clamp: only matters for huge x
%z   = mul %rc %rc
%a13 = mul 1.6059044e-10 %z            # (-1)^j / (2j + 1)!, j = 6 down to 0
%b11 = add %a13 -2.5052108e-08
%a11 = mul %b11 %z
%b9  = add %a11 2.7557319e-06
%a9  = mul %b9 %z
%b7  = add %a9 -0.0001984127
%a7  = mul %b7 %z
%b5  = add %a7 0.008333334
%a5  = mul %b5 %z
%b3  = add %a5 -0.16666667
%a3  = mul %b3 %z
%q   = add %a3 1.0
%y   = mul %rc %q
%r   = where %fin %y nan
```

## 3. Sugar

Sugar ops are shorthand. Each one **means** its expansion below, so it has no semantics of its own: a
compiler can expand it while parsing, and the result is bit-identical. Constants are expanded to the
operand's shape (`expand c shape=[...]`) when the operand isn't a scalar.

| sugar | operands | expands to |
|---|---|---|
| `neg x` | i32 or f32 | `mul x -1` (or `-1.0`) |
| `sub a b` | two i32 or two f32 | `add a (neg b)` |
| `fdiv a b` | two f32 | `mul a (recip b)`. Not correctly rounded; `div` stays i32-only. |
| `relu x` | i32 or f32 | `max x 0` (or `0.0`) |
| `exp x` | f32 | `exp2 (mul x 1.442695)` |
| `log x` | f32 | `mul (log2 x) 0.6931472` |
| `floor x` | f32 | the program below |
| `cmpeq a b` | two i32 | `where (cmplt a b) false (where (cmplt b a) false true)` |
| `cmpeq a b` | two bool | `xor (xor a b) true` |
| `matmul A B` | `M×K` and `K×N`, i32 or f32 | the week 5 composite: `reshape A [M K 1]`, `permute [1 0 2]`, `expand [K M N]`; `reshape B [K 1 N]`, `expand [K M N]`; `mul`; `reduce op=add pop=1`. Shape `M×N`. |

`(...)` above is shorthand for a separate statement. `floor`:

```
%x   = param 0 dtype=f32
%nx  = mul %x -1.0
%ax  = max %x %nx
%lt  = cmplt %ax 8388608.0
%big = xor %lt true                    # |x| >= 2^23, inf or nan: already an integer
%xc  = where %big 0.0 %x
%ti  = cast %xc dtype=i32              # truncates toward zero
%t   = cast %ti dtype=f32
%up  = cmplt %xc %t                    # a negative number was truncated up
%t1  = add %t -1.0
%fl  = where %up %t1 %t
%r   = where %big %x %fl
```

`floor -0.0` is `0.0`, and `floor` of a NaN is that NaN.

## 4. Automatic differentiation

`%g = gradient %y %x` is the derivative of `y` with respect to `x`: a value with `x`'s shape whose
element `i` is `∂y/∂x[i]`. It is computed while the program is built, as a graph of ordinary ops, so
anything a program can do with a value it can do with a gradient, including take its gradient again.

**Valid when:**

* `y` is an f32 scalar (the loss) and `x` an f32 value, neither memory.
* `x` is not a literal. Equal literals are one shared node, so "the gradient with respect to `2.0`"
  would mean every `2.0` in the program.
* Neither depends on an open range.
* Every op on a path from `x` to `y` is one the rules below cover: elementwise ops, math ops, movement
  ops, `reduce`, `stage`, `stack`, `index`, `cast`, `bitcast` and `detach`. A `call`, a `load` or a loop
  on such a path is invalid (the syllabus: autodiff works on pure graphs).
* `reduce op=mul` on such a path is invalid (it has no rule). A `shrink` of a value or an `index`
  on the path needs literal offsets.

If `y` doesn't depend on `x` at all, or only through ops whose result isn't f32 (a comparison, a cast to
i32), the gradient is all zeros. `x` itself may be anything f32, including a `load`.

**How it's computed** (reverse mode). Seed `y` with `1.0`. Visit the nodes of `y`'s graph in reverse of
their **post-order** (depth first from `y`, operands left to right, each node once, not entering call
bodies). At each node that has received gradient contributions and lies on a path to `x`, add the
contributions up in the order they arrived (`add c1 c2`, then `add` that and `c3`, ...) to get `g`, and
send each operand its share from the table, operands left to right. Only f32 operands that lie on a path
to `x` receive a share. The gradient is the sum at `x`; don't propagate past `x`.

| op | share sent to each operand, given `g` (the gradient of the op's result `u`) |
|---|---|
| `add a b` | `g`, `g` |
| `mul a b` | `mul g b`, `mul g a` |
| `max a b` | to `a`: `where (cmplt b a) g (where (cmplt a b) 0.0 (mul g 0.5))`; to `b` the same with `a` and `b` swapped. Ties split evenly. |
| `recip a` | `mul g (mul (mul u u) -1.0)` |
| `where c a b` | to `a`: `where c g 0.0`; to `b`: `where c 0.0 g`; none to `c` |
| `cast a`, `bitcast a` | `g`, when both `a` and `u` are f32 |
| `exp2 a` | `mul g (mul u 0.6931472)` |
| `log2 a` | `mul g (recip (mul a 0.6931472))` |
| `sqrt a` | `mul g (recip (mul u 2.0))` |
| `sin a` | `mul g (sin (add a 1.5707964))` |
| `detach a` | nothing |
| `stage a` | `stage g`: a staged value's gradient is staged too |
| `reshape a` | `reshape g` to `a`'s shape |
| `permute a order=p` | `permute g` by the inverse order |
| `pad a pads=[l0 r0 ...]` | `shrink g l0 l1 ...` with `a`'s shape |
| `shrink a o0 ...` (value) | `pad g` with `pads=[o0 (d0-o0-s0) ...]` (literal offsets only) |
| `expand a` | sum `g` over the grown axes: `permute` them to the front (in increasing axis order, the rest after), `reduce op=add pop=<how many>`, `reshape` to `a`'s shape. From a scalar: `reshape g [n]`, `reduce`. |
| `reduce a op=add pop=m` | `reshape g` to `[1 ... 1, rest]`, then `expand` to `a`'s shape |
| `reduce a op=max pop=m` | `hit = cast (xor (cmplt a ue) true) dtype=f32` where `ue` is `u` reshaped and expanded back to `a`'s shape; `cnt = reduce hit op=add pop=m`; then `mul (expand (mul g (recip cnt))) hit`. Ties split evenly. |
| `stack a0 ... an` | to `aj`: `index g j` |
| `index a j0 ...` | `pad (reshape g [1 ... 1, rest])` putting it at `j0, ...` (literal indices only) |

Literals in the table (`0.0`, `0.5`, `-1.0`, ...) are expanded to the right shape. Ops not in the table
(comparisons, i32 arithmetic) never carry gradient, because their results aren't f32.

Movement ops move numbers without changing them, so how you write them doesn't change any bits. What
must match exactly is the arithmetic: the shares above and the order you add contributions up in.

`detach x` is how you say "treat this as a constant". The classic use is the max subtracted for a stable
softmax: its gradient cancels out mathematically, so detaching it saves work and changes nothing in exact
math. In f32 the cancelling terms round, so the gradient's bits can differ with and without it.

## 5. Buffers from files

```
%x = buffer 3920000 dtype=f32 slot=0 url=data/mnist-train-images.f32 sha256=1ac7f6c8...
```

* `url=` is `https://...`, or a relative path (letters, digits, `_ . -`, separated by `/`, no `..`)
  resolved against the folder of the `.uir` file. It replaces `data=`; giving both is invalid.
* `sha256=` (64 lowercase hex digits) is required with `url=`. The file's SHA-256 must match, or the
  program is invalid. This is what makes a URL safe to depend on: the bytes can't change under you.
* The file holds exactly `N` elements, little-endian, with no header: 4 bytes per f32 or i32, 1 byte
  per bool (0 or 1). Any other size is invalid.
* Download each URL once and cache it (by hash). The grader's tests only use relative paths, and
  copies those files next to the program it runs.

## 6. Render and grading

`render` keeps its contract. Math ops become their bodies (or C functions doing exactly the same steps).
In C, read a float's bits with `memcpy`, not a pointer cast. Data files are the harness's job: your
kernel gets the buffers already filled, exactly as before.

New test headers:

* `# render check: slot S >= V`: instead of comparing every buffer bit for bit, the grader reads
  element 0 of slot `S` and requires it to be at least `V`. The MNIST test uses it for accuracy.
* `# time: T`: your compiler, the C compiler and the kernel each get `T` seconds instead of 10.
* `# max_bytes: B`: the rendered C may be up to `B` bytes instead of 20,000.

## 7. The MNIST program

`tests/week6/render/mnist_train.uir` trains a softmax regression (a single `784×10` layer) on the first
5000 MNIST training digits, 50 steps of 100, learning rate 1.0, then stores how many of 1000 test digits
it classifies correctly. `python tools/mnist.py program` writes it. Week 6 has no loops around whole
tensors, so every step is written out: step `k` loads batch `k` and the weights step `k - 1` stored.
The reference gets 864 right. The test needs 850.

## 8. Speed

Kernels are now big enough to time. `python tools/bench.py --compiler YOURS FILE` renders a program with
your compiler, builds and runs it, and reports the time and the useful work done, in FLOPs: one per
element of every elementwise op, and `size - result size` per `reduce`. Week 6 grades correctness and
the time limits above. The course's speed weeks build on these numbers.
