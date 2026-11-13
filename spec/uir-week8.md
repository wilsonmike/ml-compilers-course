# .uir, week 8: GPUs (provisional)

Week 8 writes kernels the way a GPU runs them: a grid of **blocks**, each a group of **threads** that share a
small, fast memory and can wait for each other. Two new loop axes describe that, and a new command, `render-cuda`,
turns such a program into CUDA. As in week 7, axes never change a result: every program still means the same as
its plain loops, so `run` and `render` (C for the CPU) work everywhere, GPU or not. Everything in weeks 1 to 7 still
holds. The course schedule names GPUs and hardware accelerators for this week, and the syllabus names the axis types
GLOBAL and LOCAL and the address spaces GLOBAL, LOCAL and ALU. The rest is our design, provisional until the
official format is published.

## 1. Two more axes

| axis | meaning | rules |
|---|---|---|
| `global` | one iteration per **block**. Blocks may run in any order, at the same time | section 2 |
| `local` | one iteration per **thread** of the current block. Its threads run at the same time | the bound is a literal from 1 to 1024, the block size |

* A `local` loop must be inside a `global` loop (directly, or inside plain loops in its body), and can't be inside
  another `local` loop. Every `local` loop in one global loop has the same bound: a kernel has one block size.
* No `thread`, `global` or `local` loop inside a `global` loop's body other than its own `local` loops.
* Every store inside a `global` loop is inside a `local` loop. A store outside would run on every thread.
* Consecutive `local` loops are **phases**. Between two phases, every thread of the block has finished the first
  before any starts the second. In CUDA that is a `__syncthreads()`. In plain loops it's automatic.

## 2. Keeping threads and blocks apart

Inside one phase the block's threads run at the same time, and blocks run at the same time as each other. So for
a phase's `local` range `t`, and for a kernel's `global` range `g`:

* **Every store, and every load of memory the same code also stores into, has a unique-number offset.** Write the
  flat offset as a sum of terms. A term is a **digit** when it's a loop index (the parallel index, or a loop inside
  the code being checked), or that index's `div` or `mod` by a literal, times a positive literal coefficient (`mul i 4`,
  `mul (div g 8) 64`, plain `t`). Terms that don't involve such a loop are the same for every thread and are
  ignored. A term that involves an inner loop but isn't a digit (say `mul i j`) counts as a digit of coefficient 1
  whose largest value is its largest minus its smallest value. A term that isn't a digit and involves the parallel
  index is invalid. Sort the digits by coefficient: each coefficient must be **greater** than the most all the smaller
  digits can add up to (`coefficient · largest value`, summed). A vector access of `k` elements adds a digit of
  coefficient 1 and largest value `k - 1`. Then the offset is a mixed-radix number, unique for every combination
  of indices, so no two threads (or blocks) touch the same element.
* The offset must **pin down the parallel index** (unless its loop has one iteration): it contains the index
  itself, or both its `div k` and its `mod k` by the same literal `k`. A `mod k` alone is enough when `k` is larger
  than the index's largest value, since then it is the index. Anything less lets two threads share a slot even
  when the coefficients pass: with 8 threads, `o[4b + (t mod 4)]` sends threads 0 and 4 to the same element.
* Every access to one buffer in that code is at the **same offset expression**: the same terms after flattening
  the `add`s, in any order (`t + 4b` and `4b + t` are the same), and the same vector size. Equal digits aren't
  enough: `sh[t]` and `sh[t + 1]` have the same digits, but thread `t` would read thread `t + 1`'s slot.
* Memory the code only reads may be read anywhere. So a later phase may read any element of shared memory an earlier
  phase wrote. A buffer is different: the kernel check covers all of a block's phases at once, because other blocks
  run at the same time, so every access to a buffer in the kernel uses one offset expression.

The phase check covers one `local` loop with the block's other indices fixed. The kernel check covers the whole
`global` body with `g` as the parallel index, skipping the block's shared memory (next point).

**Shared memory.** An alloc whose every load and store is inside one global loop is the block's shared memory:
each block starts with its own copy, all zeros (`run` re-zeroes it for every value of `g`, as week 7 does for
thread loops). An alloc used in more than one global loop, or outside one, is not shared memory: `run` and `render`
treat it like a buffer, under the same rules, and `render-cuda` exits 2 because it has nowhere to live on the GPU.

## 3. `render`

For the CPU nothing is new: render a `global` loop like week 7's `thread` loop (an outlined body run by
`uir_parallel_for`, with its shared memory declared inside), and a `local` loop as a plain loop. Phases are
consecutive loops, so the barrier between them is automatic.

## 4. `render-cuda FILE`

Prints CUDA C++. The program must be in kernel form: every computation inside a `global` loop at the top level,
and each kernel using only buffers, literals, its own ranges and its own shared memory (values computed outside a
kernel would have to come from the host, and an alloc used by two kernels has no home on the GPU). Anything else exits 2 with an `invalid:` line. The output defines:

* one `__global__` function per global loop, taking the buffers it uses, with `int32_t g = blockIdx.x`;
* the block's shared memory as `__shared__` arrays, zeroed by the threads (`for (i = threadIdx.x; i < n;
  i += blockDim.x)`) and followed by `__syncthreads()`;
* each `local` loop as a block `{ int32_t t = threadIdx.x; ... }` followed by `__syncthreads()`;
* a host function `void kernel(T *b0, ...)` with the program's buffers (device pointers), which launches the
  kernels in program order with `UIR_LAUNCH(name, grid, block, args...)`.

`UIR_LAUNCH` and nothing else comes from the harness: with real CUDA it is `name<<<grid, block>>>(args)`, and in
the emulator a loop over blocks that runs each block's threads as real threads. Device helpers (`f32_max`, ...)
are `__device__` functions. Floating point matches the CPU bit for bit, because the build uses
`nvcc -fmad=false -prec-div=true` (no fused multiply-add, IEEE division).

## 5. Grading

* `# cuda` tests run `render-cuda` and compare every buffer with the interpreter, bit for bit. With `nvcc` (or
  `--cuda-docker IMAGE`, which builds and runs in that Docker image with `--gpus all`), on the GPU. Without, in the
  emulator: the CUDA is compiled as C++ (`clang++` or `g++`), blocks run one after another, each block's threads
  are real threads, `__shared__` arrays are shared by them, and `__syncthreads()` is a real barrier. A missing
  barrier is a real race in both.
* `# cuda speed: X` tests also time your kernel against the reference kernel on the GPU (a warm-up launch, then one
  timed with CUDA events, best of 3, interleaved): at least X times its speed. Without a GPU they only check that
  your CUDA builds.
* `# cuda: invalid` tests are valid programs that aren't in kernel form: `render-cuda` must exit 2.
* `run` and `render` tests are as before.
