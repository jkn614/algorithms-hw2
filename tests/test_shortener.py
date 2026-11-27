import unittest
from functools import partial
from unittest.mock import patch

from src.shortener import URLShortener
from src.hash_table import HashTable
from src.linear_probing import LinearProbingTable

_DEFAULT_URL_SHORTENER = URLShortener


class URLShortenerTests(unittest.TestCase):
    def test_hash_table_defaults_to_hash_table(self):
        shortener = _DEFAULT_URL_SHORTENER()

        self.assertIsInstance(shortener._url_to_code, HashTable)
        self.assertIsInstance(shortener._code_to_url, HashTable)

    def test_accepts_either_table_implementation(self):
        for table_class in (HashTable, LinearProbingTable):
            with self.subTest(table_class=table_class):
                shortener = _DEFAULT_URL_SHORTENER(table_class=table_class)

                self.assertIsInstance(shortener._url_to_code, table_class)
                self.assertIsInstance(shortener._code_to_url, table_class)

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


class LinearProbingURLShortenerTests(URLShortenerTests):
    def setUp(self):
        patcher = patch(
            f"{__name__}.URLShortener",
            partial(_DEFAULT_URL_SHORTENER, table_class=LinearProbingTable),
        )
        patcher.start()
        self.addCleanup(patcher.stop)


if __name__ == "__main__":
    unittest.main()
