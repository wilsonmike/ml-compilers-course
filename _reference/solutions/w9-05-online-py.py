import math

def online(scores: list[float]) -> tuple[float, float]:
    """the running max m and sum l of exp(s - m), in one pass over the scores"""
    m, l = -math.inf, 0.0
    for s in scores:
        m_new = max(m, s)
        l = l * math.exp(m - m_new) + math.exp(s - m_new)
        m = m_new
    return m, l
