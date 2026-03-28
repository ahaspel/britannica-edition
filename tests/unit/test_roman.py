from britannica.util.roman import roman_to_int


def test_roman_to_int_basic_values() -> None:
    assert roman_to_int("I") == 1
    assert roman_to_int("V") == 5
    assert roman_to_int("X") == 10


def test_roman_to_int_subtractive_values() -> None:
    assert roman_to_int("IV") == 4
    assert roman_to_int("IX") == 9
    assert roman_to_int("XL") == 40


def test_roman_to_int_complex_value() -> None:
    assert roman_to_int("MCMXI") == 1911