# .uir, week 2: memory and rendering C (provisional)

Week 2 adds floats and memory: buffers that live outside the program, views into them, and loads and
stores. Your compiler learns to **render C** and to **run** it. Everything in [week 1](uir-week1.md) still
holds except where section 0 says otherwise; this file only adds to it. The public syllabus gives the op names
and three rules ("render loopless C functions", "loads and stores must be fully ordered", "bounds checked to never
be out of range"). The official week 2 reference isn't out yet, so the details below are our own, and they will
move to the official format when it is published.

## 0. What changes from week 1

* **Floats.** A new dtype, `f32`, with float literals and the `recip` op (section 0.1).
* **Rank-1 params and asserts.** A param may have a shape like `[3]`, a call may pass and return vectors, and an
  assert's left side may be a vector, compared against a stack literal like `[1 2 3]`.
* **List attributes.** An attribute may hold a bracketed list with spaces, like `shape=[2 3]` or `data=[1 2 3]`.
  It's one attribute, from the `[` to the `]`.
* **No budgets.** The week 1 limits (4096 bytes, 100 nodes, 300 edges, cost 1,000,000) are lifted. Week 2
  programs are bigger, and nothing is OVERBUDGET.

### 0.1 Floats

| form | regex | meaning |
|---|---|---|
| float | `-?([0-9]+\.[0-9]*\|\.[0-9]+)([eE][-+]?[0-9]+)?` or `-?[0-9]+[eE][-+]?[0-9]+` | a constant of dtype `f32` |
| special float | `inf`, `-inf`, `nan` | a constant of dtype `f32` |

A float literal is read as a 64-bit double, then rounded to f32 (round to nearest-even). Too big for f32 rounds to
`inf`; too small rounds to `0.0`. `1.0` is f32 and `1` is i32, and there is **no implicit conversion**: `add %x 1`
with `%x` an f32 is rejected. Write `add %x 1.0`, or use `cast`.

f32 is IEEE-754 binary32, rounded to nearest-even after every op. The week 1 ops that take "same" dtypes take f32
too, except `xor`, `shl`, `div` and `mod`, which stay integer ops.

| op | f32 rule |
|---|---|
| `recip a` | `1/a`, f32 only. `recip 0.0 = inf`, `recip -0.0 = -inf`. |
| `max a b` | NaN if either is NaN, and `max(-0.0, 0.0) = +0.0` in either order. |
| `cmplt a b` | Any NaN gives false. |
| `cast` | i32 to f32 rounds to nearest-even. f32 to i32 truncates toward zero and saturates: NaN is 0, anything at or past the ends of the i32 range is `INT_MIN` or `INT_MAX`. f32 to bool is `a != 0` (NaN is true). |

Bounds don't track floats: an f32 value has no useful bounds, and you can't use one as an index anyway.

For `assert`, f32 compares by value, so `0.0` equals `-0.0`, and two NaNs count as equal.

**Printing f32 constants** (for `simplify`). Print enough digits to round-trip (`%.9g` is enough for any f32) and
always include a `.` or an `e`, or the literal reads back as an i32. Print `inf`, `-inf` and `nan` exactly like
that. Simplify's equivalence check compares f32 **bit for bit**, so `0.0` and `-0.0` differ and any NaN matches any
NaN. Bugs this catches: `x * 0.0 -> 0.0` (`nan * 0.0` is `nan`) and `x + 0.0 -> x` (`-0.0 + 0.0` is `+0.0`).
`x + -0.0 -> x` is correct.

## 1. New values: memory

A memory value has dtype `bool`, `i32` or `f32`, a shape, and the **addrspace** `GLOBAL`. Every
week 1 value has addrspace `ALU`. Memory can't be an operand of an ALU op, `stack`, `index`, `call`,
or `assert`, and it can't appear inside a call body.

| op | attributes | operands | result | notes |
|---|---|---|---|---|
| `buffer n` | `dtype` (required), `slot` (required), `data` (optional) | size n ≥ 1, an integer literal | memory `(n,)` | A global buffer the program reads and writes. Slots are unique; the kernel takes buffers in slot order. `data=[v0 v1 ...]` gives exactly n initial values (literals of the buffer's dtype); without it the buffer starts as zeros. |
| `alloc n` | `dtype` (required) | size n ≥ 1, an integer literal | memory `(n,)` | Scratch memory local to the program, like `float a[10];` in C. Starts as zeros. Not an output. |
| `shrink m off` | `shape` (required) | memory m, offset `off` (i32 scalar, any expression) | memory | A view of `m` starting `off` elements in. `shape=[k]` is k elements; `shape=[]` is a single element (rank 0). |
| `load v` | none | a view (or a whole buffer) | ALU value, the view's dtype and shape | Reads memory. |
| `store v x` | none | a view (or a whole buffer), a value of the same dtype and shape | void | Writes `x` into the view. |
| `after m s` | none | memory m, a store s into m | memory, same as m | "m, once s has happened". The new version of m. `m` must be a whole version (a `buffer`, an `alloc` or an `after`), not a view. |

`shrink` of a `shrink` is allowed: offsets add up. `shape=[]` views load and store scalars. `load` and `store` also accept a whole buffer, as a view of all of it.

## 2. Versions and ordering

Memory is immutable in the graph. A store doesn't change `%b`; `after %b %s` is a **new version**
of the same storage, with the write applied. Loads read the version they're given:

```
%b  = buffer 4 dtype=i32 slot=0 data=[10 20 30 40]
%e  = shrink %b 1 shape=[]
%x  = load %e              # 20: reads the original version
%s  = store %e 99
%b1 = after %b %s          # the version after the store
%e1 = shrink %b1 1 shape=[]
%y  = load %e1             # 99
```

These rules make the order of memory operations total, which is what "fully ordered" means:

1. **One store per version.** At most one store may target any given version (through any of its
   views). Two stores into the same version are unordered, so the program is invalid.
2. **Every store is sequenced.** Each store must be the `s` of exactly one `after`, and that
   `after` must name the version the store writes into. A store nothing sequences is invalid.
3. A load of version V happens before the store that creates the next version. This is possible
   unless the load's inputs (its view's offset, say) depend on a later version of the same storage.
   Then no order works, and the program is invalid.
   (`tests/week2/run/rejected_old_version_needed_late.uir` is an example.)

The **outputs** of a program are the final version of every `buffer`: the version no `after`
builds on.

## 3. Bounds

Every view must be **provably** inside its storage, using the bounds analysis from week 1:
for `shrink m off shape=[k]` on storage of size n, the interval of `off` must satisfy
`lo ≥ 0` and `hi + k ≤ n` (`k = 1` for `shape=[]`). Values loaded from memory are unknown, so
their interval is the full i32 range. A view that can't be proven in range makes the program
invalid, and so does an `index` (week 1's rule). `mod %i 4` is provably in [0, 3], even for a negative
loaded `%i`, because `mod` floors; a raw loaded `%i` is not.

## 4. Commands

### `./compile FILE...`

Same contract as week 1: one line per file, `MATCH`, `MISMATCH` or `REJECTED` and the path. Asserts can now
read memory through loads. You may interpret the program or compile it; the grader only sees the line.
As in week 1, nothing fails at run time: division by zero is defined, a loaded value is just a value, and
every view and index has been proven in range.

### `render FILE`

Print a C translation unit to stdout that defines

```c
void kernel(T0 *b0, T1 *b1, ...);
```

with one pointer per `buffer`, in slot order. `T` is `float` for f32, `int32_t` for i32 and `bool`
for bool. When the grader calls `kernel` on buffers holding the initial `data`, the buffers must end
up holding exactly what the oracle says: f32 bit for bit (any NaN matches any NaN). `render` ignores
asserts. The C must be **loopless** (no `for`, `while`, `do`, `goto` or recursion). It may call
`<math.h>` functions, `memcpy` from `<string.h>` (to move a float's bits into an int and back), and
non-recursive helper functions defined in the same file (a `static inline` max for f32, say), and nothing
else. The file is compiled on its own, so it must `#include` what it
uses (`<stdint.h>`, `<stdbool.h>`, `<math.h>`).

The grader compiles your C with

```
clang -std=c11 -O2 -ffp-contract=off -fsanitize=undefined -fsanitize-trap=undefined
```

so the C must have **no undefined behavior**: signed overflow, `INT_MIN / -1`, oversized shifts and
reading uninitialized memory all trap. Your i32 `add` has to wrap the C way (through `uint32_t`).
C's `/` and `%` truncate, and `div` and `mod` floor, so they only agree when both sides are non-negative.
Otherwise render a small helper that adjusts the C result, and handles a zero divisor (-1 for `div`, `x` for
`mod`) and -1 (where C's `INT_MIN / -1` is undefined). `shl` shifts by `y & 31`. An f32 to i32 `cast` needs a
helper too: C's `(int32_t)x` is undefined for NaN and out-of-range values.
`-ffp-contract=off` keeps the compiler from fusing `a * b + c` into one rounding, which would break
f32 results.

Every `index` and view has been proven in range, so the C never reads past an array.

Two rules the grader can't check for you, so they're on your honor:

* **Initialize every `alloc` to zeros** (`float a[4] = {0};`). Reading uninitialized memory is undefined
  behavior, and it can pass a test by luck.
* **No recursion.** The grader rejects `for`, `while`, `do` and `goto`, but it can't see recursion.

An `alloc` whose contents never reach a buffer can be dropped from the C entirely; it changes no output.

## 5. Tests

Run tests are named as in week 1: `mismatch_` and `rejected_` prefixes, MATCH otherwise. From week 2 a `rejected_` test is also rendered: when the program itself is invalid (not just the test-file rules, like a missing assert), `render` must refuse it too, exiting 2 with an `invalid:` line. Render tests start with a
`# render` line: the grader renders them, compiles the C, runs it and compares the buffers.
