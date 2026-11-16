def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for d in range(2, n):
        if d * d > n:
            break
        if n % d == 0:
            return False
    return True
