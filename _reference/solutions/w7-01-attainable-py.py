def attainable(peak: float, bandwidth: float, flops: float, nbytes: float) -> float:
    """Best reachable GFLOP/s: limited by compute and by memory."""
    return min(peak, bandwidth * flops / nbytes)
