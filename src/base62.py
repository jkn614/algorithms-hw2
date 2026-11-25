"""Base62 conversion using the alphabet 0-9, a-z, A-Z."""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)


def encode(number: int) -> str:
    """Encode a non-negative integer as a base62 string."""
    if number < 0:
        raise ValueError("number must be non-negative")
    if number == 0:
        return "0"

    encoded = []
    while number:
        number, remainder = divmod(number, BASE)
        encoded.append(ALPHABET[remainder])
    return "".join(reversed(encoded))


def decode(code: str) -> int:
    """Decode a base62 string to a non-negative integer."""
    if not code:
        raise ValueError("code must not be empty")

    number = 0
    for character in code:
        try:
            digit = ALPHABET.index(character)
        except ValueError as error:
            raise ValueError(f"invalid base62 character: {character!r}") from error
        number = number * BASE + digit
    return number
