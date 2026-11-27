"""A string-keyed hash table using linear probing."""


class _Entry:
    __slots__ = ("key", "value")

    def __init__(self, key: str, value: object) -> None:
        self.key = key
        self.value = value


class LinearProbingTable:
    def __init__(self, capacity: int = 16, max_load: float | None = 0.75) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")
        if max_load is not None and max_load <= 0:
            raise ValueError("max_load must be positive or None")

        self._buckets: list[_Entry | None] = [None] * capacity
        self._size = 0
        self._max_load = max_load

    @property
    def capacity(self) -> int:
        return len(self._buckets)

    @staticmethod
    def _validate_key(key: object) -> None:
        if not isinstance(key, str):
            raise TypeError("keys must be strings")

    def hash_index(self, key: str) -> int:
        self._validate_key(key)
        value = 0
        for character in key:
            value = (31 * value + ord(character)) % self.capacity
        return value

    def _find_slot(self, key: str) -> tuple[_Entry | None, int | None, int]:
        self._validate_key(key)
        index = self.hash_index(key)
        for inspected in range(1, self.capacity + 1):
            entry = self._buckets[index]
            if entry is None or entry.key == key:
                return entry, index, inspected
            index = (index + 1) % self.capacity
        return None, None, self.capacity

    def find(self, key: str) -> tuple[object | None, int]:
        entry, _, inspected = self._find_slot(key)
        return (entry.value if entry is not None else None), inspected

    def put(self, key: str, value: object) -> None:
        entry, index, _ = self._find_slot(key)
        if entry is not None:
            entry.value = value
            return

        if index is None:
            if self._max_load is None:
                raise OverflowError("hash table is full")
            self._resize(self.capacity * 2)
            _, index, _ = self._find_slot(key)

        self._buckets[index] = _Entry(key, value)
        self._size += 1

        if self._max_load is not None and self.load_factor() > self._max_load:
            self._resize(self.capacity * 2)

    def get(self, key: str, default: object = None) -> object:
        entry, _, _ = self._find_slot(key)
        return entry.value if entry is not None else default

    def load_factor(self) -> float:
        return self._size / self.capacity

    def __contains__(self, key: object) -> bool:
        self._validate_key(key)
        entry, _, _ = self._find_slot(key)
        return entry is not None

    def __len__(self) -> int:
        return self._size

    def _resize(self, new_capacity: int) -> None:
        old_buckets = self._buckets
        self._buckets = [None] * new_capacity
        for entry in old_buckets:
            if entry is not None:
                _, index, _ = self._find_slot(entry.key)
                self._buckets[index] = entry
