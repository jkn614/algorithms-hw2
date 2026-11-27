"""URL shortening backed by the project's hash table."""

from urllib.parse import urlsplit

from src.base62 import encode
from src.hash_table import HashTable
from src.linear_probing import LinearProbingTable


class URLShortener:
    def __init__(
        self,
        table_class: type[HashTable] | type[LinearProbingTable] = HashTable,
    ) -> None:
        self._url_to_code = table_class()
        self._code_to_url = table_class()
        self._next_id = 1

    def shorten(self, url: str) -> str:
        self._validate_url(url)
        existing_code = self._url_to_code.get(url)
        if existing_code is not None:
            return str(existing_code)

        code = encode(self._next_id)
        self._next_id += 1
        self._url_to_code.put(url, code)
        self._code_to_url.put(code, url)
        return code

    def expand(self, code: str) -> str:
        try:
            url = self._code_to_url.get(code)
        except TypeError as error:
            raise ValueError("code must be a base62 string") from error
        if url is None:
            raise ValueError(f"unknown short code: {code!r}")
        return str(url)

    def __len__(self) -> int:
        return len(self._url_to_code)

    @staticmethod
    def _validate_url(url: str) -> None:
        if not isinstance(url, str) or not url or any(character.isspace() for character in url):
            raise ValueError("URL must be a non-empty URL without whitespace")
        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
            parsed.port
        except ValueError as error:
            raise ValueError(f"invalid URL: {url!r}") from error
        if parsed.scheme not in ("http", "https") or not hostname:
            raise ValueError("URL must have an http(s) scheme and hostname")
