def shared(uses: list[int | None]) -> bool:
    return uses[0] is not None and all(u == uses[0] for u in uses)
