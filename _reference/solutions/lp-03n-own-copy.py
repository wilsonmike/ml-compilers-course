def before_and_after(scores: list[int]) -> list[list[int]]:
    after = scores.copy()
    after.append(100)
    return [scores, after]
