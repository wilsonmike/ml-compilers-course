# .uir, week 7: memory hierarchies, kernels and threads (provisional)

Week 7 is about speed on a CPU. A program can now say **how** each loop should run: as an ordinary loop, unrolled
into straight-line code (`upcast`), or spread across threads (`thread`). None of this changes a single bit of any
result. It changes how fast the C runs, and from this week some tests grade that. Everything in weeks 1 to 6 still
holds. The course schedule names memory hierarchies, kernels and threading for this week, and the syllabus names the
axis types LOOP, UPCAST and THREAD. The rest is our design, provisional until the official format is published.

## 1. Loop axes

`range` takes an optional attribute:

```
%r = range 64 axis=thread
```

| axis | meaning | rules |
|---|---|---|
| `loop` (the default) | an ordinary loop, as in week 3 | none new |
| `upcast` | the same loop, unrolled: one copy of the body per value of `r` | the bound is a literal from 1 to 32 |
| `thread` | iterations may run at the same time, on different threads | section 2 |

`run` executes every axis as an ordinary loop, in order. The only semantic difference is private allocs (section 2).
An axis never changes the order of operations inside an iteration, so a program's results are bit for bit the same
whatever its axes say.

## 2. Thread loops

Iterations of a thread loop may run in any order, at the same time. Two iterations must therefore never touch the
same memory unless both only read it. The rules, checked statically (exit 2 when they fail):

* **No nesting.** A thread loop can't be inside another thread loop. It may be inside an ordinary loop.
* **Each iteration owns a slice.** Every store in the loop body, and every load of memory the body also stores into,
  must be at a flat offset of the form `r * S + e`:
  * `r` is the thread range, appearing in exactly one term of the offset's sum, as `r` itself (S = 1) or
    `mul r S` / `mul S r` with `S` a positive literal;
  * `e` is the sum of the other terms, none of which depends on `r`, and `0 <= e` and `e + size <= S` must be
    provable from bounds (week 1), where `size` is the number of elements accessed (1, or k for a `[k]` view).
    Bound each term on its own and add the results: `e`'s lowest value is the sum of the terms' lowest values, its
    highest the sum of their highest. (`e` is not one node in the program, so there's no single node to bound.)

  So iteration `r` only touches elements `r*S` to `r*S + S - 1`. Every access to one buffer in the loop uses the
  same `S`. Write offsets in this expanded form: `(ib*4 + i)*N + j` must be written as `ib*(4N) + i*N + j`.
* **Read-only memory is free.** Loads of memory the body never stores into may be anywhere.
* **Private allocs.** An alloc whose every load and store is inside one thread loop is private to it: every
  iteration starts with its own copy, all zeros. (`run` re-zeroes it at the start of each iteration. In an ordinary
  loop, an alloc keeps its contents from one iteration to the next.) Any other alloc is shared, and follows the same
  rules as a buffer.

## 3. Rendering

* `upcast`: emit the body once per value of `r`, with `r` a literal in each copy. This puts accumulators in
  registers: an alloc indexed only by upcast ranges becomes a set of plain variables to the C compiler.
* `thread`: move the body into its own function and call the harness:

  ```c
  void uir_parallel_for(int32_t n, void (*body)(int32_t, void *), void *ctx);
  ```

  `body(r, ctx)` must run iteration `r`. Values the body needs from outside (buffer pointers, values computed
  before the loop, enclosing ranges) travel in a struct that `ctx` points to. Private allocs are declared inside
  the function, so each call gets fresh zeros. Declare the prototype above in your C. The harness defines it.
* Buffers never alias, so a kernel may declare its parameters `restrict`.

The harness splits `0 .. n-1` into one contiguous chunk per hardware thread, with pthreads. It is compiled with
`-std=c11 -O2 -ffp-contract=off` and linked with `-lpthread`.

## 4. Grading

`run` and `render` tests work as before. Unrolled code is large, so render tests with upcast loops raise the C size
limit with `# max_bytes:`.

New: `# speed: X`. The grader renders the program with your compiler and with the reference compiler, builds both
with the harness at `-O2` (no sanitizers), and runs each three times, alternating. Your kernel must give exactly the
reference's bits, and its best time must be at most the reference's best time divided by `X`. So `# speed: 0.5`
means "at least half the reference's speed, on this machine". A test with thread loops is only timed on a machine
with at least 4 hardware threads. With fewer, it checks correctness only.

`python tools/bench.py --compiler YOURS FILE` times one program and reports FLOP/s, as in week 6.
