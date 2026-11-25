import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_round_trip(self):
        for number in (0, 1, 61, 62, 3844, 2**100):
            with self.subTest(number=number):
                self.assertEqual(decode(encode(number)), number)

    def test_zero_has_one_character_representation(self):
        self.assertEqual(encode(0), "0")
        self.assertEqual(decode("0"), 0)

    def test_negative_number_is_rejected(self):
        with self.assertRaises(ValueError):
            encode(-1)

    def test_empty_or_invalid_code_is_rejected(self):
        for code in ("", "a_", "é"):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    decode(code)


if __name__ == "__main__":
    unittest.main()
