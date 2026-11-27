def coat_check(slips: list[tuple[str, str]]) -> list[int]:
    notebook = {}
    tickets = []
    for color, size in slips:
        slip = (color, size)
        if slip in notebook:
            tickets.append(notebook[slip])
        else:
            notebook[slip] = len(notebook)
            tickets.append(notebook[slip])
    return tickets
