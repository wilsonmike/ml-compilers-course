# .uir, week 5: movement ops (provisional)

Week 5 lifts the rank limit. Values can have any rank, and four **movement ops** rearrange them without
computing anything: `reshape`, `permute`, `pad` and `shrink`. With them (plus week 4's `expand` and
`reduce`), a matrix multiply or a convolution is a few lines of movement and one `reduce`, and your
compiler can express a whole model. Everything in weeks 1 to 4 still holds, with the rank limits
removed. The syllabus names the ops and says STACK takes arbitrary inputs and SHRINK takes symbolic
parameters; the rest is our design, provisional until the official format is published.

## 1. Shapes

* A shape is a tuple of positive ints of any length. `()` is a scalar.
* **Memory stays flat.** Buffers, allocs and memory `shrink` views are still rank 0 or 1. You load a
  rank-1 value and `reshape` it; you `reshape` back to rank 1 before a `store`.
* Elementwise ALU ops, `where`, `cast` and `assert` take operands of one shared shape, any rank.
* Params keep their week 1 rule (rank 0 or 1).

## 2. Movement ops (on values)

| op | attributes | operands | result | element at index `(i0, ..., ik)` |
|---|---|---|---|---|
| `reshape x` | `shape=[d0 d1 ...]` | any value | that shape | the same element in row-major order. The element counts must match. |
| `permute x` | `order=[p0 p1 ...]` | rank-r value | `shape[k] = x.shape[p_k]` | `x` at the index whose axis `p_k` is `i_k` |
| `pad x` | `pads=[l0 r0 l1 r1 ...]` | rank-r value | each axis grows by `l + r` | `x[i - l]` where every axis is inside, else zero (`0`, `0.0` or `false`) |
| `shrink x o0 ... o(r-1)` | `shape=[s0 ...]` | rank-r value, r offsets (i32 scalars) | that shape | `x[i0 + o0, ..., ik + ok]` |
| `expand x` | `shape=[...]` | a scalar, or a value of the same rank | that shape | `x` with each size-1 axis read at 0 |
| `stack a0 ... a(n-1)` | none | values of one shape | `(n,) + shape` | `a_{i0}[i1, ...]` |
| `index x j0 ... j(m-1)` | none | rank ≥ m, i32 scalars | drops m leading axes | `x[j0, ..., j(m-1), i0, ...]`, each `j` in range at run time |
| `reduce x` | `op` (`add`, `mul`, `max`), `pop=m` (default 1) | rank ≥ m | drops m leading axes | a left fold over the m leading axes, in row-major order, starting from the first element |

`shrink` on a value is a different op from `shrink` on memory (week 2): the first operand decides.
Its offsets may be any i32 expression (symbolic), and as with views they must be **provably** in range:
for every axis, `o_k`'s interval must satisfy `lo ≥ 0` and `hi + s_k ≤ x.shape[k]`.

`pads` must be ≥ 0. To cut, use `shrink`.

## 3. Composite ops

Some familiar ops aren't primitives; you build them from these. A matrix multiply `A (M×K) @ B (K×N)`:

```
%a3 = reshape %A shape=[M K 1]
%aT = permute %a3 order=[1 0 2]         # K M 1
%ax = expand %aT shape=[K M N]
%b3 = reshape %B shape=[K 1 N]
%bx = expand %b3 shape=[K M N]
%p  = mul %ax %bx
%C  = reduce %p op=add pop=1            # M N: sums over k, in order k = 0, 1, ...
```

This is the syllabus's GEMM example, with the transpose written out.

## 4. Rangeify

`render` turns every movement op into index arithmetic on the way to week 3 loops:
`reshape` becomes a flatten and an unflatten with `mul`, `div` and `mod`; `permute` reorders indices;
`pad` reads a clamped index and selects zero outside with `where`; `shrink` adds offsets; `expand`
reads size-1 axes at 0; `reduce` over m axes becomes one accumulator loop. The 20,000-byte limit and
the bit-exact comparison still apply.

**On your honor:** a padded read must be clamped into range even though the mask throws its value away.
Reading past a buffer is undefined behavior in C whether or not you use the result, and the grader
can't see it (the masked value never reaches an output). Clamp first, then mask.

## 5. Test headers

Same as weeks 2 to 4.
