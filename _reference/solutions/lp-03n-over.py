def over(nums: list[int], limit: int) -> list[int]:
    big = []
    for n in nums:
        if n > limit:
            big.append(n)
    return big
