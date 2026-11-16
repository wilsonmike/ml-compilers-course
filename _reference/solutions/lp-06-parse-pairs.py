def parse_pairs(text):
    result = {}
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        key, eq, value = line.partition("=")
        key = key.strip()
        if not eq or not key:
            raise ValueError(f"bad line {n}: {line!r}")
        result[key] = value.strip()
    return result
