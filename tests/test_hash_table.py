import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def test_collisions_are_stored_and_comparisons_are_counted(self):
        table = HashTable(initial_capacity=8)
        table["a"] = 1
        table["i"] = 2

        self.assertEqual(table["a"], 1)
        self.assertEqual(table.last_probe_count, 1)
        self.assertEqual(table["i"], 2)
        self.assertEqual(table.last_probe_count, 2)
        self.assertEqual(table.last_probe_slots, [1])

    def test_overwrite_does_not_increase_size(self):
        table = HashTable()
        table["key"] = 1
        table["key"] = 2

        self.assertEqual(len(table), 1)
        self.assertEqual(table["key"], 2)

    def test_resize_preserves_entries(self):
        table = HashTable(initial_capacity=2)
        table["first"] = 1
        table["second"] = 2
        table["third"] = 3

        self.assertGreater(table.capacity, 2)
        self.assertEqual([table[key] for key in ("first", "second", "third")], [1, 2, 3])

    def test_delete_and_missing_key(self):
        table = HashTable()
        table["key"] = "value"
        del table["key"]

        self.assertNotIn("key", table)
        with self.assertRaises(KeyError):
            table["key"]
        with self.assertRaises(KeyError):
            del table["key"]

    def test_rejects_non_string_keys_and_invalid_capacity(self):
        with self.assertRaises(TypeError):
            HashTable()[1] = "value"
        with self.assertRaises(ValueError):
            HashTable(initial_capacity=0)


if __name__ == "__main__":
    unittest.main()
