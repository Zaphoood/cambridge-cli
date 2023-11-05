def roman(num: int) -> str:
    # I = 1
    # V = 5
    # X = 10
    # L = 50
    # C = 100
    # D = 500
    # M = 1000
    assert num > 0
    out = ""

    out += (num // 1000) * "M"
    num = num % 1000

    out += _to_digit_pair(num // 100, ones="C", fives="D", tens="M")
    num = num % 100

    out += _to_digit_pair(num // 10, ones="X", fives="L", tens="C")
    num = num % 10

    out += _to_digit_pair(num, ones="I", fives="V", tens="X")

    return out


def _to_digit_pair(num: int, ones: str, fives: str, tens: str) -> str:
    assert 0 <= num <= 9
    assert len(ones) == len(fives) == len(tens) == 1

    if num == 0:
        return ""
    if 1 <= num <= 3:
        return ones * num
    if num == 4:
        return ones + fives
    if 5 <= num <= 8:
        return fives + ones * (num - 5)
    if num == 9:
        return ones + tens

    raise Exception("Unreachable")
