def call_site(id: int, n: int, fields: list[str]) -> str:
    return f"{{ thread{id}_ctx k_ = {{ {', '.join(fields)} }}; uir_parallel_for({n}, thread{id}, &k_); }}"
