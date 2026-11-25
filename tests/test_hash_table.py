import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def test_default_capacity_and_core_interface(self):
        table = HashTable()

        self.assertEqual(len(table._buckets), 16)
        self.assertEqual(table.load_factor(), 0)
        self.assertIsNone(table.get("missing"))
        self.assertEqual(table.get("missing", "default"), "default")
        self.assertNotIn("missing", table)

        table.put("key", "first")
        table.put("key", "updated")

        self.assertEqual(len(table), 1)
        self.assertIn("key", table)
        self.assertEqual(table.get("key"), "updated")
        self.assertEqual(table.load_factor(), 1 / 16)

    def test_find_returns_value_and_number_of_compared_nodes(self):
        table = HashTable(max_load=None)
        table.put("a", 1)
        table.put("q", 2)

        first_value, first_comparisons = table.find("a")
        second_value, second_comparisons = table.find("q")

        self.assertEqual((first_value, second_value), (1, 2))
        self.assertIn((first_comparisons, second_comparisons), ((1, 2), (2, 1)))

    def test_collision_chain_uses_linked_nodes(self):
        table = HashTable(max_load=None)
        table.put("a", 1)
        table.put("q", 2)

        head = table._buckets[1]
        self.assertIsNotNone(head)
        self.assertNotIsInstance(head, list)
        second = head.next
        self.assertIsNotNone(second)
        self.assertNotIsInstance(second, list)
        self.assertIsNone(second.next)
        self.assertEqual(
            sorted(((head.key, head.value), (second.key, second.value))),
            [("a", 1), ("q", 2)],
        )
        self.assertEqual(table.get("a"), 1)
        self.assertEqual(table.get("q"), 2)

    def test_table_doubles_capacity_after_load_limit_is_exceeded(self):
        table = HashTable()
        for index in range(12):
            table.put(f"key-{index}", index)
        self.assertEqual(len(table._buckets), 16)

        table.put("key-12", 12)

        self.assertEqual(len(table._buckets), 32)
        self.assertEqual(len(table), 13)
        for index in range(13):
            self.assertEqual(table.get(f"key-{index}"), index)

    def test_none_max_load_keeps_capacity_fixed(self):
        table = HashTable(capacity=16, max_load=None)
        for index in range(32):
            table.put(f"key-{index}", index)

        self.assertEqual(len(table._buckets), 16)
        self.assertEqual(len(table), 32)
        self.assertEqual(table.load_factor(), 2)

    def test_find_missing_key_counts_all_nodes_in_chain(self):
        table = HashTable(max_load=None)
        table.put("a", 1)
        table.put("q", 2)

        value, comparisons = table.find("A")

        self.assertIsNone(value)
        self.assertEqual(comparisons, 2)
if __name__ == "__main__":
    unittest.main()
