_ROMAN_VALUES: dict[str, int] = {
    "I": 1,
    "V": 5,
    "X": 10,
    "L": 50,
    "C": 100,
    "D": 500,
    "M": 1000,
}


def roman_to_int(value: str) -> int:
    total = 0
    prev = 0

    for ch in reversed(value.upper()):
        current = _ROMAN_VALUES[ch]
        if current < prev:
            total -= current
        else:
            total += current
            prev = current

    return total