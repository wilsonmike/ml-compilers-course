def ordered(stores: list[tuple[str, str]], afters: list[tuple[str, str, str]]) -> bool:
    seen = set()
    for _, version in stores:
        if version in seen:
            return False
        seen.add(version)
    for name, version in stores:
        named = [m for _, m, s in afters if s == name]
        if named != [version]:
            return False
    return True
