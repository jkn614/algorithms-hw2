import http.client
import threading
import unittest
from http.server import HTTPServer
from urllib.parse import urlencode

from src import server as server_module
from src.shortener import URLShortener


class URLShortenerServerTests(unittest.TestCase):
    def setUp(self):
        self.original_shortener = server_module.SHORTENER
        server_module.SHORTENER = URLShortener()
        self.httpd = HTTPServer(("127.0.0.1", 0), server_module.ShortenerHandler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()
        server_module.SHORTENER = self.original_shortener

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection(
            "127.0.0.1", self.httpd.server_port, timeout=2
        )
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        result = response.status, response.getheaders(), response.read().decode()
        connection.close()
        return result

    def test_home_page_has_url_form_and_table_link(self):
        status, _, body = self.request("GET", "/")

        self.assertEqual(status, 200)
        self.assertIn('action="/" method="post"', body)
        self.assertIn('name="url"', body)
        self.assertIn('href="/table"', body)

    def test_shortens_url_and_redirects_short_code(self):
        payload = urlencode({"url": "https://example.com/article"})
        status, _, body = self.request(
            "POST",
            "/",
            body=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        self.assertEqual(status, 200)
        self.assertIn('href="/1"', body)
        self.assertIn("/1", body)

        status, headers, _ = self.request("GET", "/1")

        self.assertEqual(status, 302)
        self.assertIn(("Location", "https://example.com/article"), headers)

    def test_invalid_url_shows_error_and_unknown_code_is_not_found(self):
        payload = urlencode({"url": "ftp://example.com"})
        status, _, body = self.request(
            "POST",
            "/",
            body=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        self.assertEqual(status, 400)
        self.assertIn("http(s)", body)
        self.assertEqual(self.request("GET", "/unknown")[0], 404)

    def test_table_page_shows_buckets_chains_and_hash_steps(self):
        for url in (
            "https://example.com/article",
            "https://example.com/articlE",
        ):
            payload = urlencode({"url": url})
            self.request(
                "POST",
                "/",
                body=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        status, _, body = self.request("GET", "/table")

        self.assertEqual(status, 200)
        self.assertIn("URL-to-code index", body)
        self.assertIn("Code-to-URL index", body)
        self.assertIn("https://example.com/article", body)
        self.assertIn("Horner", body)
        self.assertIn("<details>", body)
        self.assertIn("→", body)


if __name__ == "__main__":
    unittest.main()
