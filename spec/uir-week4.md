# .uir, week 4: rangeify, reduce, materialization (provisional)

In weeks 1 to 3 every ALU op worked on scalars, and loops were written by hand with `range` and `end`.
Week 4 lets you write whole-vector programs, with ALU ops on rank-1 values, `reduce`, `expand` and
`stage`, and makes your compiler turn them into loops itself. That transformation is **rangeify**:
it removes shapes from every op by giving each element an index from a range. Everything in weeks 1 to
3 still holds. The syllabus names REDUCE, STAGE and EXPAND and says "rangeify removes shapes from all
ops" and that materialization must be confronted; the rest is our design, provisional until the
official format is published. Shapes are still rank 0 or 1 (rank 2 arrives in week 5).

## 1. What changes

* **ALU ops accept rank-1 operands** of the same shape `(n,)` and work elementwise. There is still no
  implicit broadcasting: `add %v 1.0` with `%v` of shape `(4,)` is a type error. Broadcast with `expand`.
* `load` of a whole buffer, or of a `[k]` view, gives a rank-1 value (as in week 2), and `store` of a
  rank-1 value writes all of it.

## 2. New ops

| op | attributes | operands | result | notes |
|---|---|---|---|---|
| `expand x` | `shape` (required, `[n]`) | a scalar (week 5 widens this to any value whose size-1 axes grow) | `(n,)` | Every element equals `x`. Growing an axis that isn't size 1 is always an error. |
| `reduce x` | `op` (required: `add`, `mul` or `max`) | a rank-1 value `(n,)` | `()` | A left fold: `x[0] op x[1] op ... op x[n-1]`, in that order, starting from `x[0]`. |
| `stage x` | none | any value | same as `x` | Same value. Tells the compiler to **materialize** `x`: compute it once into a temp buffer, and read the buffer wherever `x` is used. |

The fold order matters for f32 (rounding happens after every step) and the grader compares f32 bit for
bit, so your reduce must accumulate left to right, starting from the first element. For `max`, NaN
semantics are week 1's: any NaN makes the result NaN.

Rank-1 values may not depend on an open range from a hand-written week 3 loop.

## 3. Rangeify and materialization

`run` can evaluate rank-1 values directly. `render` must not unroll them: a rank-1 value of size
4096 has to become a loop. Rangeify gives every element an index:

* an elementwise op at index `i` is the op applied to its operands at index `i`
* `load` of a view at index `i` is a scalar load at `offset + i`
* `expand x` at index `i` is just `x`
* `reduce x` becomes a loop that folds `x` at each index into an accumulator
* `store` of a rank-1 value becomes a loop that stores each element

When a value is used in two places (say `%y = reduce %x op=add`, then `%z = div` of `%x` by the sum),
rangeify can **recompute** it at each use (fusion: no memory traffic, more arithmetic) or
**materialize** it once into a temp buffer (fission: one extra pass over memory, no repeated work).
Without `stage`, you may choose either; `stage` forces materialization. Either way the results must be
identical, because elementwise ops are deterministic and every reduce folds in the same order.

## 4. Commands and grading

`run` and `render` keep their contracts. Render tests now include large sizes, and the grader requires
the rendered C to be **at most 20,000 bytes**, so unrolling a 4096-element vector fails. `render` may
use `for` loops whenever the program has a `range`, a `reduce`, `expand` or `stage`, an elementwise op
on a rank-1 value, or any rank-1 value with more than 32 elements. Programs with none of these (week 2
style) must still render loopless.

As in week 3, only an `after` with no open ranges is a buffer's output. A loop whose stores only reach
an `after` inside the loop changes no buffer. Week 6 will start timing kernels; week 4 only checks correctness and size.

## 5. Test headers

Same as weeks 2 and 3: `# expect: ...` for run tests, `# render` for render tests.
