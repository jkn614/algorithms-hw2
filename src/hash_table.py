"""A string-keyed hash table using separate chaining and Horner hashing."""

from collections.abc import Iterator


class HashTable:
    def __init__(
        self, initial_capacity: int = 8, max_load_factor: float = 0.75
    ) -> None:
        if initial_capacity < 1:
            raise ValueError("initial_capacity must be positive")
        if max_load_factor <= 0:
            raise ValueError("max_load_factor must be positive")

        self._buckets: list[list[tuple[str, object]]] = [
            [] for _ in range(initial_capacity)
        ]
        self._size = 0
        self._max_load_factor = max_load_factor
        self.last_probe_count = 0
        self.last_probe_slots: list[int] = []

    @property
    def capacity(self) -> int:
        return len(self._buckets)

    @property
    def buckets(self) -> tuple[tuple[tuple[str, object], ...], ...]:
        return tuple(tuple(bucket) for bucket in self._buckets)

    def hash_steps(self, key: str) -> list[tuple[str, int, int]]:
        self._validate_key(key)
        value = 0
        steps = []
        for character in key:
            previous = value
            value = (31 * value + ord(character)) % self.capacity
            steps.append((character, previous, value))
        return steps

    def hash_index(self, key: str) -> int:
        steps = self.hash_steps(key)
        return steps[-1][2] if steps else 0

    def _validate_key(self, key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("keys must be strings")

    def _find(self, key: str) -> int | None:
        self._validate_key(key)
        bucket_index = self.hash_index(key)
        self.last_probe_slots = [bucket_index]
        self.last_probe_count = 0
        for entry_index, (stored_key, _) in enumerate(self._buckets[bucket_index]):
            self.last_probe_count += 1
            if stored_key == key:
                return entry_index
        return None

    def __getitem__(self, key: str) -> object:
        entry_index = self._find(key)
        if entry_index is None:
            raise KeyError(key)
        return self._buckets[self.last_probe_slots[0]][entry_index][1]

    def __setitem__(self, key: str, value: object) -> None:
        self._validate_key(key)
        entry_index = self._find(key)
        bucket_index = self.last_probe_slots[0]
        if entry_index is not None:
            self._buckets[bucket_index][entry_index] = (key, value)
            return

        if (self._size + 1) / self.capacity > self._max_load_factor:
            self._resize(self.capacity * 2)
            bucket_index = self.hash_index(key)
        self._buckets[bucket_index].append((key, value))
        self._size += 1

    def __delitem__(self, key: str) -> None:
        entry_index = self._find(key)
        if entry_index is None:
            raise KeyError(key)
        del self._buckets[self.last_probe_slots[0]][entry_index]
        self._size -= 1

    def __contains__(self, key: object) -> bool:
        self._validate_key(key)
        return self._find(key) is not None

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[str]:
        for bucket in self._buckets:
            for key, _ in bucket:
                yield key

    def items(self) -> Iterator[tuple[str, object]]:
        for bucket in self._buckets:
            yield from bucket

    def get(self, key: str, default: object = None) -> object:
        entry_index = self._find(key)
        if entry_index is None:
            return default
        return self._buckets[self.last_probe_slots[0]][entry_index][1]

    def _resize(self, new_capacity: int) -> None:
        old_items = list(self.items())
        self._buckets = [[] for _ in range(new_capacity)]
        self._size = 0
        for key, value in old_items:
            bucket_index = self.hash_index(key)
            self._buckets[bucket_index].append((key, value))
            self._size += 1
