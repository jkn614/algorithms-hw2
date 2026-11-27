import http.client
import threading
import unittest
from http.server import HTTPServer
from urllib.parse import urlencode

from src import server as server_module
from src.linear_probing import LinearProbingTable
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

    def use_linear_shortener(self):
        original_linear_shortener = server_module.LINEAR_SHORTENER
        server_module.LINEAR_SHORTENER = URLShortener(
            table_class=LinearProbingTable
        )
        self.addCleanup(
            setattr, server_module, "LINEAR_SHORTENER", original_linear_shortener
        )

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

    def test_result_and_table_links_use_forwarded_origin(self):
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "localhost:8000",
            "X-Forwarded-Host": "codespaces.example",
            "X-Forwarded-Proto": "https",
        }
        payload = urlencode({"url": "https://example.com/article"})
        status, _, body = self.request("POST", "/", body=payload, headers=headers)

        self.assertEqual(status, 200)
        self.assertIn('href="https://codespaces.example/1"', body)
        self.assertIn(">https://codespaces.example/1</a>", body)

        status, _, body = self.request(
            "GET",
            "/table",
            headers={
                "Host": "localhost:8000",
                "X-Forwarded-Host": "codespaces.example",
                "X-Forwarded-Proto": "https",
            },
        )

        self.assertEqual(status, 200)
        self.assertIn('href="https://codespaces.example/1"', body)
        self.assertIn(">https://codespaces.example/1</a>", body)

    def test_result_link_falls_back_to_host_header(self):
        payload = urlencode({"url": "https://example.com/article"})
        status, _, body = self.request(
            "POST",
            "/",
            body=payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "shortener.example:8000",
            },
        )

        self.assertEqual(status, 200)
        self.assertIn('href="https://shortener.example:8000/1"', body)

    def test_result_link_uses_forwarded_protocol(self):
        payload = urlencode({"url": "https://example.com/article"})
        status, _, body = self.request(
            "POST",
            "/",
            body=payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "localhost:8000",
                "X-Forwarded-Host": "codespaces.example",
                "X-Forwarded-Proto": "http",
            },
        )

        self.assertEqual(status, 200)
        self.assertIn('href="http://codespaces.example/1"', body)
        self.assertIn(">http://codespaces.example/1</a>", body)

    def test_navigation_is_present_on_default_and_linear_pages(self):
        self.use_linear_shortener()

        for path in ("/", "/table", "/linear", "/linear/table"):
            with self.subTest(path=path):
                status, _, body = self.request("GET", path)

                self.assertEqual(status, 200)
                self.assertIn('href="/">기본 홈</a>', body)
                self.assertIn('href="/table">기본 해시 테이블</a>', body)
                self.assertIn('href="/linear">선형 탐지 홈</a>', body)
                self.assertIn(
                    'href="/linear/table">선형 탐지 테이블</a>', body
                )

    def test_linear_shortener_page_shows_full_link_and_redirects(self):
        self.use_linear_shortener()
        payload = urlencode({"url": "https://example.com/linear"})
        status, _, body = self.request(
            "POST",
            "/linear",
            body=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        self.assertEqual(status, 200)
        self.assertIn('href="https://127.0.0.1:', body)
        self.assertIn(">https://127.0.0.1:", body)
        self.assertIn("/linear/s/1</a>", body)

        status, headers, _ = self.request("GET", "/linear/s/1")

        self.assertEqual(status, 302)
        self.assertIn(("Location", "https://example.com/linear"), headers)

    def test_linear_table_shows_slots_hash_and_probe_counts(self):
        self.use_linear_shortener()
        urls = (
            "https://example.com/item-0",
            "https://example.com/item-20",
        )
        for url in urls:
            payload = urlencode({"url": url})
            self.request(
                "POST",
                "/linear",
                body=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        status, _, body = self.request("GET", "/linear/table")

        self.assertEqual(status, 200)
        self.assertIn("Linear probing table", body)
        for url in urls:
            self.assertIn(url, body)
        self.assertIn("비어 있음", body)
        self.assertIn("Initial slot", body)
        self.assertIn("Actual slot", body)
        self.assertIn("Slots inspected", body)
        self.assertIn("Horner hash calculation", body)
        self.assertEqual(body.count("<p><strong>Initial slot:</strong> 7</p>"), 2)
        self.assertIn("<p><strong>Actual slot:</strong> 7</p>", body)
        self.assertIn("<p><strong>Actual slot:</strong> 8</p>", body)
        self.assertIn("<p><strong>Slots inspected:</strong> 1</p>", body)
        self.assertIn("<p><strong>Slots inspected:</strong> 2</p>", body)


if __name__ == "__main__":
    unittest.main()
