def calc_polyorder(window: int, max_poly: int = 3) -> int:
    return min(window - 1, max_poly)
