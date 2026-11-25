"""A string-keyed hash table using linked-list separate chaining."""

from collections.abc import Iterator


class _Node:
    __slots__ = ("key", "value", "next")

    def __init__(self, key: str, value: object) -> None:
        self.key = key
        self.value = value
        self.next: _Node | None = None


class HashTable:
    def __init__(self, capacity: int = 16, max_load: float | None = 0.75) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")
        if max_load is not None and max_load <= 0:
            raise ValueError("max_load must be positive or None")

        self._buckets: list[_Node | None] = [None] * capacity
        self._size = 0
        self._max_load = max_load

    @property
    def capacity(self) -> int:
        return len(self._buckets)

    @property
    def buckets(self) -> tuple[_Node | None, ...]:
        return tuple(self._buckets)

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

    @staticmethod
    def _validate_key(key: object) -> None:
        if not isinstance(key, str):
            raise TypeError("keys must be strings")

    def _find_node(self, key: str) -> tuple[_Node | None, int, int]:
        self._validate_key(key)
        bucket_index = self.hash_index(key)
        node = self._buckets[bucket_index]
        comparisons = 0
        while node is not None:
            comparisons += 1
            if node.key == key:
                return node, comparisons, bucket_index
            node = node.next
        return None, comparisons, bucket_index

    def find(self, key: str) -> tuple[object | None, int]:
        node, comparisons, _ = self._find_node(key)
        return (node.value if node is not None else None), comparisons

    def put(self, key: str, value: object) -> None:
        node, _, bucket_index = self._find_node(key)
        if node is not None:
            node.value = value
            return

        new_node = _Node(key, value)
        new_node.next = self._buckets[bucket_index]
        self._buckets[bucket_index] = new_node
        self._size += 1

        if self._max_load is not None and self.load_factor() > self._max_load:
            self._resize(self.capacity * 2)

    def get(self, key: str, default: object = None) -> object:
        node, _, _ = self._find_node(key)
        return node.value if node is not None else default

    def load_factor(self) -> float:
        return self._size / self.capacity

    def __contains__(self, key: object) -> bool:
        self._validate_key(key)
        node, _, _ = self._find_node(key)
        return node is not None

    def __len__(self) -> int:
        return self._size

    def __getitem__(self, key: str) -> object:
        node, _, _ = self._find_node(key)
        if node is None:
            raise KeyError(key)
        return node.value

    def __setitem__(self, key: str, value: object) -> None:
        self.put(key, value)

    def __delitem__(self, key: str) -> None:
        self._validate_key(key)
        bucket_index = self.hash_index(key)
        previous = None
        node = self._buckets[bucket_index]
        while node is not None:
            if node.key == key:
                if previous is None:
                    self._buckets[bucket_index] = node.next
                else:
                    previous.next = node.next
                self._size -= 1
                return
            previous = node
            node = node.next
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        for head in self._buckets:
            node = head
            while node is not None:
                yield node.key
                node = node.next

    def items(self) -> Iterator[tuple[str, object]]:
        for head in self._buckets:
            node = head
            while node is not None:
                yield node.key, node.value
                node = node.next

    def _resize(self, new_capacity: int) -> None:
        old_buckets = self._buckets
        self._buckets = [None] * new_capacity
        for head in old_buckets:
            node = head
            while node is not None:
                next_node = node.next
                bucket_index = self.hash_index(node.key)
                node.next = self._buckets[bucket_index]
                self._buckets[bucket_index] = node
                node = next_node
