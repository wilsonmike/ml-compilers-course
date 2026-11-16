def most_common(words: list[str]) -> tuple[str, int] | None:
    if not words:
        return None
    counts = {}
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    return sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[0]
