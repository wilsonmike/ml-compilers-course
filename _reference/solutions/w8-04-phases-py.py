def fuse_phases(phases: list[list[str]], names: list[str]) -> list[str]:
    """phases[k]: the C statements of local loop k, which uses the variable names[k].
    Return the CUDA kernel body: each phase as { int32_t name = threadIdx.x; ...statements } then __syncthreads();"""
    out = []
    for stmts, n in zip(phases, names):
        out.append("{")
        out.append(f"  int32_t {n} = threadIdx.x;")
        out += ["  " + s for s in stmts]
        out.append("}")
        out.append("__syncthreads();")
    return out
