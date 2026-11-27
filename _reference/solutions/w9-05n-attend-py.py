import math

def attend(pairs: list[tuple[float, float]]) -> float:
    m, l, acc = -math.inf, 0.0, 0.0
    for s, v in pairs:
        m_new = max(m, s)
        c = math.exp(m - m_new)
        p = math.exp(s - m_new)
        l = l * c + p
        acc = acc * c + p * v
        m = m_new
    return acc / l
