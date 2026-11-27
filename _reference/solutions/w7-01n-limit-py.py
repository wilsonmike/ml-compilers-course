def limit(peak: float, bandwidth: float, flops: float, nbytes: float) -> str:
    intensity = flops / nbytes
    memory_limit = bandwidth * intensity
    if memory_limit < peak:
        return "memory"
    return "compute"
