def blocks_per_sm(threads: int, regs: int, shared_kb: int) -> int:
    if threads > 1024 or regs > 255 or shared_kb > 48:
        return 0
    return min(65536 // (threads * regs), 1536 // threads, 100 // shared_kb)
