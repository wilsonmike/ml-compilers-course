import math


def c_float(x: float) -> str:
    if math.isnan(x):
        return "NAN"
    if math.isinf(x):
        return "INFINITY" if x > 0 else "(-INFINITY)"
    mant, exp = x.hex().split("p")  # '0x1.4000000000000', '+1'
    return mant.rstrip("0").rstrip(".") + "p" + exp + "f"
