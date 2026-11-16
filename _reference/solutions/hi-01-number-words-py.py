def number_words(words: list[str]) -> list[int]:
    table: dict[str, int] = {}
    out = []
    for w in words:
        if w not in table:
            table[w] = len(table)
        out.append(table[w])
    return out
