def inverse_order(order: list[int]) -> list[int]:
    """The order that undoes permute(order=order)."""
    inv = [0] * len(order)
    for k, p in enumerate(order):
        inv[p] = k
    return inv


def summed_axes(x_shape: list[int], out_shape: list[int]) -> list[int]:
    """The axes that expand x_shape -> out_shape grew: its gradient sums over them."""
    return [k for k, (a, b) in enumerate(zip(x_shape, out_shape)) if a == 1 and b != 1]
