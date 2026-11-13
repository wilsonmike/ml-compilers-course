# .uir, week 9: GPUs part 2 (provisional)

Week 9 makes GPU kernels fast. Two things carry most of the speed of a real GEMM, convolution or attention kernel:
keeping each thread's working set in **registers**, and the **tensor cores**, units that multiply small matrices in
one step. This week adds a rule that lets `render-cuda` use registers, and three things for tensor cores: the `i8`
dtype, the `warp` axis and the `mma` op. As always, none of it changes a result: `run` and `render` still work
everywhere, and `render-cuda` must still give the interpreter's bits. Everything in weeks 1 to 8 still holds. The
course schedule names tensor cores, upcasting, fast GEMMs, convolutions and flash attention for this week. The rest
is our design, provisional until the official format is published.

## 1. Per-thread memory

Week 8 made every alloc used inside one global loop the block's shared memory. Some of it only ever holds one
thread's data. An alloc of a kernel is **per-thread** when:

* every load and store of it is inside a `local` loop (none in a `warp` loop, none an `mma` operand), and
* each one is at an offset `t * S + e`, by week 7's slice rule: `t` is that local loop's range, `S` a positive
  literal, the same `S` for every access, and `0 <= e` and `e + size <= S` provable.

Then thread `t` only ever touches elements `t*S` to `t*S + S - 1`, whichever phase it's in. Nothing about the
program's meaning changes (it's still shared memory, zero at the start of each block), but `render-cuda` may give
each thread its own array of `S` elements, zeroed at the start of the kernel, and index it by `e`. When every `e` is
a literal (an `upcast` loop does that), the CUDA compiler keeps the array in **registers**. The reference compiler
does this, and the speed tests expect it.

A later phase that reads another thread's slice (`(t + 1) * S + e`, say) breaks the rule: that alloc stays in
shared memory.

## 2. Tensor cores

### `i8`

A fourth dtype, for memory: 8-bit two's complement, -128 to 127.

* `buffer` and `alloc` take `dtype=i8`. A `data=` literal is an integer from -128 to 127. A `url=` file has one byte
  per element.
* `load` of i8 memory gives an i8 value, and `store` takes one.
* `cast X dtype=i8` takes an `i32` (or an `i8`, unchanged) and keeps its low 8 bits (`200` becomes `-56`). `cast` from i8 to `i32`, `f32`
  or `bool` is exact.
* There are no i8 literals or `const`s, and arithmetic and comparisons don't take i8: cast to `i32` to compute. Ops
  that only move values (`where`, `stack`, `index`, `assert` and the shape ops) take it like any dtype.
* Only `buffer`, `alloc` and `cast` accept `dtype=i8`. Any other op given it exits 2, `param` and `bitcast`
  included. A cast to i8 from `f32` or `bool` exits 2 too.

### `mma`

```
%e = mma %C %A %B lda=K ldb=N ldc=N
```

`mma` is an effect, like `store`: it adds the product of two 16x16 tiles into a third.

* `C` is `i32` memory, `A` and `B` are `i8` memory. Each is a buffer or alloc version, or a scalar view
  (`shrink ... shape=[]`) whose offset is where the tile starts.
* `lda`, `ldb` and `ldc` are each tile's row stride: row `i` of `A`'s tile starts `i * lda` elements after its first
  element. Each is a positive literal multiple of 16 (16, 32, 48, ...). Zero exits 2.
* For `i` and `j` from 0 to 15, `C[i][j] = C[i][j] + A[i][0]*B[0][j] + ... + A[i][15]*B[15][j]`, in `i32` with
  wraparound (the order doesn't matter: products of i8 values fit, and wrapping addition is associative).
* `after %C %e` names the new version of `C`, and `end` repeats an `mma` as it does a store. Like a load, the `mma`
  reads the versions of `A`, `B` and `C` it names, so a later store into one of them waits for it.
* Static rules (exit 2):
  * every tile is provably inside its memory: offset `>= 0`, and offset + `15 * ld + 16` at most the memory's size;
  * every term of the `A` and `B` offsets is a provable multiple of 32, and every term of the `C` offset a provable
    multiple of 8. That's 32 bytes, the alignment the tensor cores load from. A term is a **provable multiple** of
    `k` when it is a literal divisible by `k`, an `add` of two provable multiples, or a `mul` with at least one
    factor a provable multiple. Nothing smarter: `mul (mul k 2) 16` is a multiple of 32 in fact, but neither factor
    is, so it exits 2. Write `mul k 32`.
* Inside a week 7 `thread` loop, an `mma` follows the slice rule like a store, with `size` the whole tile:
  `15 * ld + 16` elements. That covers its `C`, and its `A` or `B` when the loop also writes that memory.

### `warp`

```
%w = range 4 axis=warp
```

A `warp` loop is a phase, like a `local` loop, run by whole **warps**: iteration `w` by warp `w`, the 32 threads
with `threadIdx.x / 32 == w`. The bound is a literal from 1 to 32. A warp loop of `n` makes the block `32n` threads,
and every `local` and `warp` loop of one kernel must agree on the block size.

* A `warp` loop is inside a `global` loop. Phases don't nest: no `warp` or `local` loop inside a `local` or `warp`
  loop, in either order.
* Inside a global loop, an `mma` must be inside a `warp` loop: the 32 threads of a warp run it together. A store must
  be inside a `local` loop, not a `warp` loop: in a warp loop it would run on all 32 threads.
* The week 8 rules apply with `w` as the parallel index. An `mma` writes its `C` tile, which adds two digits to its
  offset: `ldc` with largest value 15 (the row), and 1 with largest value 15 (the column). So warps writing tiles
  of one matrix must place them a whole tile apart. The same two digits (with `lda` or `ldb`) apply to an `A` or
  `B` tile whenever the check covers it, that is when the same code also writes that memory.
* Week 8's one-offset-expression rule counts the tile as part of the expression: an `mma` tile and a plain load
  or store of the same memory are different layouts even at the same offset, and so are two tiles with different
  row strides.

`run` executes a warp loop as an ordinary loop, as always.

## 3. `render`

For the CPU, a `warp` loop is a plain loop, and `mma` is 256 dot products of length 16 (a triple loop of 16), wrapping like `add`
(compute in `uint32_t`). An `i8` is an `int8_t`.

## 4. `render-cuda`

* A `warp` loop is a block `{ int32_t w = threadIdx.x / 32; ... }` followed by `__syncthreads()`.
* An `mma` uses the warp-level matrix API, `wmma` (the harness includes `<mma.h>` and says `using namespace nvcuda;`,
  so don't include it yourself). Load the three tiles into fragments (`matrix_a` and `matrix_b` are `signed char`,
  `row_major`; the accumulator is `int`, loaded and stored with `mem_row_major`), `mma_sync`, `store_matrix_sync`,
  then `__syncwarp()` so the warp sees its own stores before it loads `C` again.
* Declare shared memory `__shared__ __align__(32)`, so tiles in it are aligned.
* Per-thread memory (section 1) may be a plain array in each thread, `T a[S] = {0};` at the top of the kernel.

The build adds `-arch=native`: tensor cores need the GPU's own architecture (`sm_72` or newer for i8).

## 5. Grading

As in week 8. The emulator runs `wmma` on the CPU: every thread of the warp computes the whole tile, and lane 0
stores it, between two warp barriers. `__syncwarp()` is a real barrier for the warp's 32 threads.

`# cuda speed: X` tests now include an int8 GEMM on tensor cores, a register-tiled f32 GEMM, a convolution and
flash attention. Without a GPU they only check that your CUDA builds.
