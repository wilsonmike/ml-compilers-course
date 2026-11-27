def atom(word: str) -> int | str:
    if word.startswith("%"):
        return word[1:]
    return int(word)


def parse_line(line: str) -> tuple[str, str, int | str, int | str]:
    words = line.split()
    name = words[0][1:]
    op = words[2]
    x = atom(words[3])
    y = atom(words[4])
    return (name, op, x, y)
