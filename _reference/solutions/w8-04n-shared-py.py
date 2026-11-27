def shared_lines(ty: str, name: str, n: int) -> list[str]:
    return [f"__shared__ {ty} {name}[{n}];",
            f"for (int32_t z_ = threadIdx.x; z_ < {n}; z_ += blockDim.x) {name}[z_] = 0;",
            "__syncthreads();"]
