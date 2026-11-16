def count_digits(n: int) -> int:
    count = 1
    while n >= 10:
        n = n // 10
        count = count + 1
    return count
