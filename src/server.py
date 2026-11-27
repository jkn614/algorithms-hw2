"""HTTP interface for the in-memory URL shortener."""

import argparse
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, quote, unquote, urlsplit

from src.hash_table import HashTable
from src.linear_probing import LinearProbingTable
from src.shortener import URLShortener

SHORTENER = URLShortener()
LINEAR_SHORTENER = URLShortener(table_class=LinearProbingTable)
MAX_FORM_BYTES = 16_384


def _page(title: str, content: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font: 16px system-ui, sans-serif; line-height: 1.5; margin: 2rem auto; max-width: 70rem; padding: 0 1rem; color: #172033; }}
    nav {{ display: flex; gap: 1rem; margin-bottom: 2rem; }}
    input[type=url] {{ box-sizing: border-box; display: block; margin: .5rem 0 1rem; padding: .7rem; width: min(100%, 42rem); }}
    button {{ padding: .65rem 1rem; }}
    .error {{ color: #a11; }}
    .result, .node {{ border: 1px solid #cbd5e1; border-radius: .5rem; margin: .8rem 0; padding: 1rem; overflow-wrap: anywhere; }}
    .buckets {{ list-style: none; padding: 0; }}
    .bucket {{ border-top: 1px solid #d6dbe4; padding: .7rem 0; }}
    .chain {{ align-items: stretch; display: flex; flex-wrap: wrap; gap: .5rem; }}
    .node {{ background: #f8fafc; margin: .3rem 0; max-width: 30rem; }}
    .arrow {{ align-self: center; font-size: 1.5rem; }}
    details {{ margin-top: .6rem; }}
    pre {{ overflow-wrap: anywhere; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <nav>
    <a href="/">기본 홈</a>
    | <a href="/table">기본 해시 테이블</a>
    | <a href="/linear">선형 탐지 홈</a>
    |
    <a href="/linear/table">선형 탐지 테이블</a>
  </nav>
  <main><h1>{html.escape(title)}</h1>{content}</main>
</body>
</html>"""


class ShortenerHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/":
            self._send_html(200, _page("URL shortener", self._form()))
            return
        if path == "/table":
            try:
                content = self._table()
            except ValueError as error:
                self._send_html(
                    400, _page("Invalid request", self._form(str(error)))
                )
                return
            self._send_html(200, _page("Hash table", content))
            return
        if path == "/linear":
            self._send_html(
                200,
                _page(
                    "Linear probing URL shortener",
                    self._form(action="/linear", short_path_prefix="/linear/s/"),
                ),
            )
            return
        if path == "/linear/table":
            self._send_html(
                200,
                _page(
                    "Linear probing table",
                    self._linear_table(),
                ),
            )
            return
        if path.startswith("/linear/s/"):
            code_path = path[len("/linear/s/") :]
            if not code_path or "/" in code_path:
                self._not_found()
                return
            code = unquote(code_path)
            try:
                url = LINEAR_SHORTENER.expand(code)
            except ValueError:
                self._not_found()
                return
            self._redirect(url)
            return
        if path.startswith("/linear/"):
            self._not_found()
            return
        if not path.startswith("/") or "/" in path[1:]:
            self._not_found()
            return

        code = unquote(path[1:])
        try:
            url = SHORTENER.expand(code)
        except ValueError:
            self._not_found()
            return

        self._redirect(url)

    def _redirect(self, url: str) -> None:
        self.send_response(302)
        self.send_header("Location", url)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        if path not in ("/", "/linear"):
            self._not_found()
            return
        shortener = SHORTENER if path == "/" else LINEAR_SHORTENER
        form_action = path
        short_path_prefix = "/" if path == "/" else "/linear/s/"

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_html(
                400,
                _page(
                    "Invalid request",
                    self._form(
                        "Invalid form data.",
                        action=form_action,
                        short_path_prefix=short_path_prefix,
                    ),
                ),
            )
            return
        if content_length <= 0 or content_length > MAX_FORM_BYTES:
            self._send_html(
                400,
                _page(
                    "Invalid request",
                    self._form(
                        "Invalid form data.",
                        action=form_action,
                        short_path_prefix=short_path_prefix,
                    ),
                ),
            )
            return

        try:
            encoded_form = self.rfile.read(content_length).decode("utf-8")
            fields = parse_qsl(encoded_form, keep_blank_values=True, max_num_fields=16)
        except (UnicodeDecodeError, ValueError):
            self._send_html(
                400,
                _page(
                    "Invalid request",
                    self._form(
                        "Invalid form data.",
                        action=form_action,
                        short_path_prefix=short_path_prefix,
                    ),
                ),
            )
            return

        url = ""
        for name, value in fields:
            if name == "url":
                url = value
                break

        try:
            code = shortener.shorten(url)
        except ValueError as error:
            self._send_html(
                400,
                _page(
                    "URL shortener",
                    self._form(
                        str(error),
                        entered_url=url,
                        action=form_action,
                        short_path_prefix=short_path_prefix,
                    ),
                ),
            )
            return

        try:
            content = self._form(
                code=code,
                action=form_action,
                short_path_prefix=short_path_prefix,
            )
        except ValueError as error:
            self._send_html(
                400,
                _page(
                    "Invalid request",
                    self._form(
                        str(error),
                        entered_url=url,
                        action=form_action,
                        short_path_prefix=short_path_prefix,
                    ),
                ),
            )
            return
        self._send_html(200, _page("URL shortened", content))

    def _first_header_value(self, name: str) -> str:
        return self.headers.get(name, "").split(",", 1)[0].strip()

    def _short_link(self, code: str, short_path_prefix: str = "/") -> str:
        forwarded_host = self._first_header_value("X-Forwarded-Host")
        host = forwarded_host or self._first_header_value("Host")
        scheme = self._first_header_value("X-Forwarded-Proto") or "https"
        scheme = scheme.lower()

        if scheme not in ("http", "https"):
            raise ValueError("Invalid forwarded protocol.")
        if (
            not host
            or any(character.isspace() or character in "/\\?#@" for character in host)
        ):
            raise ValueError("Invalid host header.")
        try:
            parsed_host = urlsplit(f"//{host}")
            parsed_host.port
        except ValueError as error:
            raise ValueError("Invalid host header.") from error
        if (
            parsed_host.hostname is None
            or parsed_host.path
            or parsed_host.query
            or parsed_host.fragment
            or parsed_host.username is not None
            or parsed_host.password is not None
            or parsed_host.netloc != host
        ):
            raise ValueError("Invalid host header.")

        return f"{scheme}://{host}{short_path_prefix}{quote(code, safe='')}"

    def _form(
        self,
        error: str = "",
        entered_url: str = "",
        code: str = "",
        action: str = "/",
        short_path_prefix: str = "/",
    ) -> str:
        error_section = (
            f'<p class="error" role="alert">{html.escape(error)}</p>' if error else ""
        )
        result_section = ""
        if code:
            short_link = self._short_link(code, short_path_prefix)
            local_path = short_path_prefix + quote(code, safe="")
            result_section = (
                '<section class="result"><h2>Short link</h2>'
                f'<p><a href="{html.escape(short_link, quote=True)}">'
                f"{html.escape(short_link)}</a></p>"
                f'<p><a href="{html.escape(local_path, quote=True)}">'
                f"Open on this server ({html.escape(local_path)})</a></p>"
                "</section>"
            )
        return (
            f"{error_section}"
            f'<form action="{html.escape(action, quote=True)}" method="post">'
            '<label for="url">URL to shorten</label>'
            f'<input id="url" name="url" type="url" required value="{html.escape(entered_url, quote=True)}">'
            '<button type="submit">Shorten</button>'
            "</form>"
            f"{result_section}"
        )

    @staticmethod
    def _hash_steps(table: HashTable, key: str) -> str:
        steps = table.hash_steps(key)
        if not steps:
            return "<li>Empty key maps to bucket 0.</li>"
        details = []
        for character, previous, current in steps:
            safe_character = html.escape(character)
            details.append(
                "<li>"
                f"h = (31 × {previous} + ord('{safe_character}') "
                f"[{ord(character)}]) % {table.capacity} = {current}"
                "</li>"
            )
        return "".join(details)

    def _render_index(self, title: str, table: HashTable, url_keys: bool) -> str:
        output = [f"<h2>{html.escape(title)}</h2>", '<ol class="buckets">']
        for index, head in enumerate(table.buckets):
            output.append(
                f'<li class="bucket"><strong>Bucket {index}</strong>'
            )
            if head is None:
                output.append("<p>empty</p></li>")
                continue

            output.append('<div class="chain">')
            node = head
            is_first = True
            while node is not None:
                if not is_first:
                    output.append('<span class="arrow" aria-label="next node">→</span>')

                if url_keys:
                    url = node.key
                    code = str(node.value)
                    key_label = "URL key"
                else:
                    code = node.key
                    url = str(node.value)
                    key_label = "Code key"

                short_link = self._short_link(code)
                output.append(
                    '<article class="node">'
                    f"<p><strong>{key_label}:</strong> "
                    f"<code>{html.escape(node.key)}</code></p>"
                    f"<p><strong>URL:</strong> {html.escape(url)}</p>"
                    f"<p><strong>Short code:</strong> {html.escape(code)}</p>"
                    f'<p><strong>Short link:</strong> <a href="{html.escape(short_link, quote=True)}">{html.escape(short_link)}</a></p>'
                    "<details><summary>Horner hash calculation</summary>"
                    "<ol>"
                    f"{self._hash_steps(table, node.key)}"
                    "</ol></details>"
                    "</article>"
                )
                node = node.next
                is_first = False

            output.append("</div></li>")
        output.append("</ol>")
        return "".join(output)

    def _table(self) -> str:
        return (
            self._render_index(
                "URL-to-code index", SHORTENER._url_to_code, url_keys=True
            )
            + self._render_index(
                "Code-to-URL index", SHORTENER._code_to_url, url_keys=False
            )
        )

    @staticmethod
    def _linear_hash_steps(table: LinearProbingTable, key: str) -> str:
        value = 0
        details = []
        for character in key:
            previous = value
            value = (31 * value + ord(character)) % table.capacity
            details.append(
                "<li>"
                f"h = (31 × {previous} + ord('{html.escape(character)}') "
                f"[{ord(character)}]) % {table.capacity} = {value}"
                "</li>"
            )
        if not details:
            return "<li>Empty key maps to slot 0.</li>"
        return "".join(details)

    def _linear_table(self) -> str:
        table = LINEAR_SHORTENER._url_to_code
        output = ['<ol class="buckets">']
        for index, entry in enumerate(table._buckets):
            output.append(f'<li class="bucket"><strong>Slot {index}</strong>')
            if entry is None:
                output.append("<p>비어 있음</p></li>")
                continue

            url = entry.key
            code = str(entry.value)
            initial_slot = table.hash_index(url)
            _, inspected = table.find(url)
            short_link = self._short_link(code, "/linear/s/")
            output.append(
                '<article class="node">'
                f"<p><strong>URL:</strong> {html.escape(url)}</p>"
                f"<p><strong>Short code:</strong> {html.escape(code)}</p>"
                f'<p><strong>Short link:</strong> <a href="{html.escape(short_link, quote=True)}">{html.escape(short_link)}</a></p>'
                f"<p><strong>Initial slot:</strong> {initial_slot}</p>"
                f"<p><strong>Actual slot:</strong> {index}</p>"
                f"<p><strong>Slots inspected:</strong> {inspected}</p>"
                "<details><summary>Horner hash calculation</summary>"
                "<ol>"
                f"{self._linear_hash_steps(table, url)}"
                "</ol></details>"
                "</article></li>"
            )
        output.append("</ol>")
        return "".join(output)

    def _send_html(self, status: int, content: str) -> None:
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _not_found(self) -> None:
        self._send_html(
            404,
            _page(
                "Not found",
                '<p>The short link was not found. <a href="/">Return home</a>.</p>',
            ),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener web server.")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    with HTTPServer(("127.0.0.1", args.port), ShortenerHandler) as server:
        print(f"Serving URL shortener on http://127.0.0.1:{args.port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
