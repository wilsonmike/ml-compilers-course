# .uir, week 3: loops (provisional)

Week 3 adds loops. With `range` and `end` you can write a matrix multiply and a convolution by hand,
and your renderer emits `for` loops. Everything in [week 1](uir-week1.md) and [week 2](uir-week2.md)
still holds, except that rendered C may now contain `for` loops. The syllabus names the ops (RANGE,
END) and says ranges must be ordered properly; the rest is our design, provisional until the official
format is published.

## 1. Ops

| op | attributes | operands | result | notes |
|---|---|---|---|---|
| `range n` | none | n: an i32 scalar with no open ranges | i32 `()` | A loop counter: takes the values `0, 1, ..., n-1`. The statement's name is the range's name. `n ≤ 0` runs zero times. |
| `end x1 ... xk r` | none | one or more effects, then a range | effect | Runs the effects `x1 ... xk` once for every value of `r`, in increasing order. Closes `r`. |

An **effect** is a `store` or an `end`. Effects have dtype `void`. Besides `end`, the only things
that may consume an effect are `after` (week 2) and `end`.

## 2. Open ranges

Every UOp has a set of **open ranges**: the ranges it depends on that haven't been closed.

* A `range` is open in itself. Any other op's open ranges are the union of its operands' open ranges.
* `end x1 ... xk r` removes `r`: its open ranges are those of the effects, minus `r`.
* `after m e` may sit inside loops (a reset store followed by an inner loop is a chain of versions
  inside the outer loops). Only an `after` with **no** open ranges counts as a buffer's output version;
  the afters inside loops are local to an iteration. When `e` is an `end`, the loop must store into `m`
  itself: each of its stores into that buffer writes into version `m`, or into a version built on `m`
  inside the loop. Naming an older version of the buffer is invalid, just as it is for a single store
  (week 2). That keeps each buffer's versions one chain, so its output version is never ambiguous.
* An `assert`, a `call` (and everything in a call body), a `buffer`/`alloc` size and a `range` bound
  must have no open ranges.
* Every range a store depends on must be closed by an `end` before an `after` uses it, and
  `end ... r` must actually depend on `r` (closing a range the effect doesn't use is an error).
* Ranges nest the way the ends do: if an effect is inside `end ... r1`, and that end is inside
  `end ... r2`, then `r2` is the outer loop. Each range is closed by exactly one end, so the nesting
  is always well defined. A loop body may ignore an outer range (it then repeats identically).

## 3. Memory inside loops

A loop body runs again and again over the same storage. Where a value is computed is decided by the
ranges it depends on: inside every loop whose range it uses, and no deeper. A `load` is the one
exception, and the rule is:

> A load is placed like any other value: inside every loop whose range it depends on, and no deeper.
> The one exception: take the innermost loop that contains **every use** of the load. If that loop is
> deeper than the load's own place, and it stores into the version the load reads, the load moves into
> it, runs on every iteration, and sees the **current** contents: the previous iteration's store, or
> the contents before the loop on the first iteration.
>
> A use is inside a loop only if it is placed there itself: because it depends on the loop's range, or
> because it is a load that this same rule moved there. `add %cur 1.0` depends on no range, so it sits
> outside the loop, and so does its load.

If the uses are split, some inside the loop and some outside, the load runs outside the loop and
every use sees the contents from before the loop.

**Watch for the pinned load.** "Every use" means every use. If you also use the accumulator's load
in something that doesn't depend on the range (say `%dbg = add %cur 1.0`, kept for an assert), the
innermost loop holding all uses is the outer block, so the load runs once, before the loop, and the
accumulator silently stops accumulating. Give the loop its own load. That's what makes an accumulator work:

```
%acc  = alloc 1 dtype=f32
%k    = range 4
%a    = shrink %acc 0 shape=[]
%cur  = load %a                 # previous iteration's sum (0.0 on the first)
%x    = ...                     # this iteration's product, depends on %k
%sum  = add %cur %x
%s    = store %a %sum
%e    = end %s %k               # repeat the store for k = 0..3
%acc1 = after %acc %e           # the accumulator after the whole loop
```

Here `%cur` doesn't depend on `%k`, but its only use (`%sum`) is inside the `k` loop, and that loop
stores into the version `%cur` reads, so `%cur` is loaded fresh every iteration. To reset an
accumulator once per output element, make the reset store depend on the outer ranges, for example by
accumulating straight into the output at offset `i*N + j` (lesson 3.3 builds a matmul this way).

Within **one** iteration the week 2 rules hold: one store per version, and loads of a version run
before the store that overwrites it. Bounds are proven as before; a range's interval is `[0, n-1]`
(with `n`'s upper bound), so `i*K + k` is provably inside a `K*N` buffer when `i < N` and `k < K`.

## 4. Commands

`run` and `render` keep their week 2 contracts. `render` may now emit `for` loops (and only `for`
loops: still no `while`, `goto` or recursion). Values that don't depend on a range should be computed
outside it; the grader doesn't measure this in week 3, but week 6 will time your kernels.

## 5. Test headers

Same as week 2: `# expect: ...` for run tests, `# render` for render tests.
