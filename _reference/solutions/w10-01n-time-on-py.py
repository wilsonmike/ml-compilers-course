def time_on(n: int, work: int, mb: int, speed: int) -> int:
    if n == 1:
        return work
    return work // n + mb // speed
