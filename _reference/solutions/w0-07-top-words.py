def top_words(k: int, words: list[str]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    return sorted(counts.items(), key=lambda wn: (-wn[1], wn[0]))[:k]
