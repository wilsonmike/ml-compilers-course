# .uir, week 10: multiple GPUs and sharding (provisional)

Week 10 runs one program on several GPUs. A new loop axis says which device runs which iterations, and a rule
decides where each piece of memory lives: cut into **shards**, one per device, or copied whole to every device.
`render-cuda` then has a new job, moving memory between devices. As always, an axis never changes a result:
`./compile` and `render` treat a device loop as a plain loop, so every program still means the same as its plain
loops, on one GPU, several, or none. Everything in weeks 1 to 9 still holds. The course schedule names multiple GPUs
and sharding for this week. The rest is our design, provisional until the official format is published.

## 1. The `device` axis

```
%d = range 4 axis=device
```

One iteration per device: iteration `d` runs on device `d`. Different devices run at the same time.

* The bound is a literal from 1 to 16, the number of devices.
* A device loop is at the top level: not inside any other loop.
* A device runs kernels. Inside a device loop, the parallel loops are `global` loops with their `local` and `warp`
  loops, under the rules of weeks 8 and 9. A `thread` loop inside a device loop is rejected.
* The device index is an ordinary i32 value and may be used in arithmetic, like any range.

## 2. Where memory lives

Devices don't share memory. So for each buffer a device loop touches, the compiler has to know which device needs
which part of it. The rule reuses week 7's slice rule, with the device range `d` in place of the thread range.

* **Memory the loop writes is sharded.** Every load and store of it inside the device loop is at an offset
  `d * S + e`: `S` a positive literal, the same `S` for every access to that buffer, and `0 <= e` and
  `e + size <= S` provable. Then device `d` only ever touches elements `d*S` to `d*S + S - 1`, its **shard**. An
  `mma` tile counts with its whole extent, as in week 9.
* **The shards fit.** `N * S` is at most the buffer's size, with `N` the device loop's bound. Elements past the last
  shard belong to no device and keep their values.
* **Memory the loop only reads may be read anywhere.** When every read of it follows the slice rule with one `S`
  and the shards fit, it is sharded too. Otherwise it is **replicated**: every device gets a copy of all of it.
* An alloc that is one kernel's shared memory (week 8) lives on that kernel's device and is outside this rule. An
  alloc used by more than one kernel is treated like a buffer, as in week 8.

These are static rules. A program that breaks them is REJECTED, and `render` exits 2.

Two device loops in one program may shard the same buffer differently. Between them, and before and after them,
all memory is whole again (section 4).

## 3. `render`

For the CPU nothing is new: a device loop is a plain loop, and the kernels inside it render as in week 8.

## 4. `render-cuda`

The program must be in kernel form, as in week 8, with one addition: a `global` loop may also sit directly inside a
top-level device loop. Inside a device loop but outside a kernel, the only work allowed is i32 `add` and `mul` on
the device index and literals (a shard's offset, for instance). The host computes those and passes them to the
kernels. Anything else there exits 2. As in week 8, a value that depends on none of a kernel's ranges is placed outside that kernel, so a load of one fixed element (`x[0]`, say) ends up on the host and is refused: load it inside the kernel at an offset that uses the kernel's ranges, or pass the value in another buffer.

The buffers passed to `kernel(...)` live on device 0, and must be complete there again when it returns. For each
device loop the host function:

1. **Scatters.** For every device `d` and every buffer the loop touches, allocates memory on device `d` and copies
   in the device's shard (`S` elements starting at `d * S`), or the whole buffer when it is replicated. A buffer the
   loop only writes is copied in too: new memory is not zeroed, and step 4 copies the whole shard back, so elements
   the kernels do not write must arrive with their old values.
2. **Launches.** For every device, selects it and launches the loop's kernels in program order. A kernel takes its
   device's allocations in place of the buffers, plus the device index and any host-computed values it uses. Inside
   the kernel a sharded buffer holds only the shard, so element `d * S + e` of the buffer is element `e` of the
   allocation.
3. **Waits** for every device to finish.
4. **Gathers.** Copies every written shard back to its place in the buffer on device 0, and frees the allocations.

Global loops outside a device loop run on device 0, as in week 8.

Five names come from the harness:

| name | meaning |
|---|---|
| `UIR_ALLOC(d, bytes)` | allocate on device `d`. The memory is not zeroed |
| `UIR_COPY(dst_dev, dst, src_dev, src, bytes)` | copy between two devices, or within one |
| `UIR_DEVICE(d)` | launches after this go to device `d` |
| `UIR_SYNC()` | wait for every device to finish its kernels |
| `UIR_FREE(d, p)` | free an allocation |

With real CUDA these are `cudaSetDevice`, `cudaMalloc`, `cudaMemcpyPeer`, `cudaDeviceSynchronize` and `cudaFree`.
A machine with fewer GPUs than the program has devices still runs it: device `d` is GPU `d` modulo the number of
GPUs, each with its own allocations.

## 5. Grading

* `# cuda` tests are graded as in week 8: every buffer must match the oracle's, bit for bit.
* In the emulator each device's memory is separate and starts filled with a pattern, so a kernel that reads
  something that was never copied to its device gets wrong bits. The emulator also stops a kernel that is launched
  on a device other than 0 with a pointer to memory it did not allocate on that device, a copy that names the wrong
  device, and a write just past either end of a device's allocation (it checks a few guard bytes when the memory is
  freed). It does not catch every out-of-range access: a read outside an allocation, or a write far from one, is
  not reported. The static rules of section 2 are what keep accesses in range.
* `# cuda copy: N` tests also count the bytes `UIR_COPY` moves and fail above `N`. `N` is what the reference
  moves. That is how a compiler that copies whole buffers to every device, where a shard would do, is told apart
  from one that shards: their results are the same.
* Run and render tests are as before.
