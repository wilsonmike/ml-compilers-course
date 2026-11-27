def kernel_open(k: int, counter: str, params: list[tuple[str, str]]) -> list[str]:
    ps = ", ".join(f"{ty} *__restrict__ {b}" for ty, b in params)
    return [f"__global__ void k{k}({ps}) {{",
            f"  int32_t {counter} = blockIdx.x;"]


def launch(k: int, blocks: int, threads: int, bufs: list[str]) -> str:
    return f"UIR_LAUNCH(k{k}, {blocks}, {threads}, {', '.join(bufs)});"
