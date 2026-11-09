# .uir, week 2: memory and rendering C (provisional)

Week 2 adds memory: buffers that live outside the program, views into them, and loads and stores.
Your compiler learns to **render C** and to **run** it. Everything in [week 1](uir-week1.md) still
holds; this file only adds to it. The public syllabus gives the op names and three rules ("render
loopless C functions", "loads and stores must be fully ordered", "bounds checked to never be out of
range"). The details below are our own and will move to the official format when it is published.

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
| `after m s` | none | memory m, a store s into m | memory, same as m | "m, once s has happened". The new version of m. |

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
3. A load of version V happens before the store that creates the next version. (Values can't
   depend on the future, so this is always possible.)

The **outputs** of a program are the final version of every `buffer`: the version no `after`
builds on.

## 3. Bounds

Every view must be **provably** inside its storage, using the bounds analysis from week 1:
for `shrink m off shape=[k]` on storage of size n, the interval of `off` must satisfy
`lo ≥ 0` and `hi + k ≤ n` (`k = 1` for `shape=[]`). Values loaded from memory are unknown, so
their interval is the full i32 range. A view that can't be proven in range makes the program
invalid. `mod (max %i 0) 4` is provably in [0, 3]; a raw loaded `%i` is not.

## 4. Commands

### `run FILE`

Same contract as week 1 (exit 0 / 1 / 2, stderr lines). Asserts can now read memory through loads.
You may interpret the program or compile it; the grader only sees the exit code and stderr.

### `render FILE`

Print a C translation unit to stdout that defines

```c
void kernel(T0 *b0, T1 *b1, ...);
```

with one pointer per `buffer`, in slot order. `T` is `float` for f32, `int32_t` for i32 and `bool`
for bool. When the grader calls `kernel` on buffers holding the initial `data`, the buffers must end
up holding exactly what the oracle says: f32 bit for bit (any NaN matches any NaN). `render` ignores
asserts. The C must be **loopless** (no `for`, `while`, `goto` or recursion). It may call
`<math.h>` functions and non-recursive helper functions defined in the same file (a `static inline`
max for f32, say), and nothing else.

The grader compiles your C with

```
clang -std=c11 -O2 -ffp-contract=off -fsanitize=undefined -fsanitize-trap=undefined
```

so the C must have **no undefined behavior**: signed overflow, `INT_MIN / -1`, oversized shifts and
reading uninitialized memory all trap. Your i32 `add` has to wrap the C way (through `uint32_t`).
`-ffp-contract=off` keeps the compiler from fusing `a * b + c` into one rounding, which would break
f32 results.

Programs in render tests have no runtime errors, so an `index` is always in range (out of range would be
undefined behavior in C).

Two rules the grader can't check for you, so they're on your honor:

* **Initialize every `alloc` to zeros** (`float a[4] = {0};`). Reading uninitialized memory is undefined
  behavior, and it can pass a test by luck.
* **No recursion.** The grader rejects `for`, `while`, `do` and `goto`, but it can't see recursion.

An `alloc` whose contents never reach a buffer can be dropped from the C entirely; it changes no output.

## 5. Test headers

```
# expect: pass | assert_fail | invalid     (run tests, as in week 1)
# render                                   (render tests: compile, run, compare buffers)
```
