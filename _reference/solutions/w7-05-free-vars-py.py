def free_vars(body: list[tuple[str, list[str]]], loop_var: str) -> list[str]:
    """Names the body uses but does not define (other than loop_var), sorted."""
    defined = {name for name, _ in body}
    return sorted({u for _, uses in body for u in uses if u not in defined and u != loop_var})
