def cooking_order(needs: dict[str, list[str]], dish: str) -> list[str]:
    done: set[str] = set()
    order: list[str] = []

    def visit(item: str) -> None:
        if item in done:
            return
        done.add(item)
        for part in needs.get(item, []):
            visit(part)
        order.append(item)

    visit(dish)
    return order
