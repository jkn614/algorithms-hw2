import unittest

from src.shortener import URLShortener


class URLShortenerTests(unittest.TestCase):
    def test_shortens_and_expands_url(self):
        shortener = URLShortener()
        code = shortener.shorten("https://example.com/a")

        self.assertEqual(code, "1")
        self.assertEqual(shortener.expand(code), "https://example.com/a")

    def test_same_url_reuses_code(self):
        shortener = URLShortener()

        self.assertEqual(shortener.shorten("https://example.com"), "1")
        self.assertEqual(shortener.shorten("https://example.com"), "1")
        self.assertEqual(len(shortener), 1)

    def test_rejects_invalid_urls(self):
        shortener = URLShortener()
        for url in ("", "ftp://example.com", "https://", "https://example.com:bad"):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    shortener.shorten(url)

    def test_unknown_or_invalid_code_is_rejected(self):
        shortener = URLShortener()
        for code in ("z", "", "_"):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    shortener.expand(code)


if __name__ == "__main__":
    unittest.main()
