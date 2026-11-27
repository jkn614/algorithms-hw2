import unittest

from src.hash_table import HashTable
from src.linear_probing import LinearProbingTable


class HashTableTests(unittest.TestCase):
    table_class = HashTable

    def test_default_capacity_and_core_interface(self):
        table = self.table_class()

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
        table = self.table_class(max_load=None)
        table.put("a", 1)
        table.put("q", 2)

        first_value, first_comparisons = table.find("a")
        second_value, second_comparisons = table.find("q")

        self.assertEqual((first_value, second_value), (1, 2))
        self.assertIn((first_comparisons, second_comparisons), ((1, 2), (2, 1)))

    def test_collision_chain_uses_linked_nodes(self):
        table = self.table_class(max_load=None)
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
        table = self.table_class()
        for index in range(12):
            table.put(f"key-{index}", index)
        self.assertEqual(len(table._buckets), 16)

        table.put("key-12", 12)

        self.assertEqual(len(table._buckets), 32)
        self.assertEqual(len(table), 13)
        for index in range(13):
            self.assertEqual(table.get(f"key-{index}"), index)

    def test_none_max_load_keeps_capacity_fixed(self):
        table = self.table_class(capacity=16, max_load=None)
        for index in range(32):
            table.put(f"key-{index}", index)

        self.assertEqual(len(table._buckets), 16)
        self.assertEqual(len(table), 32)
        self.assertEqual(table.load_factor(), 2)

    def test_find_missing_key_counts_all_nodes_in_chain(self):
        table = self.table_class(max_load=None)
        table.put("a", 1)
        table.put("q", 2)

        value, comparisons = table.find("A")

        self.assertIsNone(value)
        self.assertEqual(comparisons, 2)


class LinearProbingTests(HashTableTests):
    table_class = LinearProbingTable

    @unittest.skip("Linear probing does not use linked collision chains")
    def test_collision_chain_uses_linked_nodes(self):
        pass

    @unittest.skip("A linear-probing table cannot hold more entries than slots")
    def test_none_max_load_keeps_capacity_fixed(self):
        pass

    @unittest.skip("A missing-key probe also inspects the first empty slot")
    def test_find_missing_key_counts_all_nodes_in_chain(self):
        pass

    def test_probe_wraps_from_last_slot_to_zero(self):
        table = self.table_class(capacity=4, max_load=None)
        table.put("c", 1)
        table.put("g", 2)

        self.assertEqual(table._buckets[3].key, "c")
        self.assertEqual(table._buckets[0].key, "g")
        self.assertEqual(table.find("g"), (2, 2))

    def test_full_table_without_growth_raises_on_insert(self):
        table = self.table_class(capacity=2, max_load=None)
        table.put("a", 1)
        table.put("b", 2)

        with self.assertRaises(OverflowError):
            table.put("c", 3)

        self.assertEqual(len(table._buckets), 2)
        self.assertEqual(len(table), 2)

    def test_colliding_keys_are_placed_in_the_next_slot(self):
        table = self.table_class(capacity=8, max_load=None)
        table.put("a", 1)
        table.put("i", 2)

        self.assertEqual(table.find("a"), (1, 1))
        self.assertEqual(table.find("i"), (2, 2))
    def test_find_missing_key_counts_slots_until_empty(self):
        table = self.table_class(capacity=8, max_load=None)
        table.put("a", 1)
        table.put("i", 2)

        value, inspected = table.find("q")

        self.assertIsNone(value)
        self.assertEqual(inspected, 3)
if __name__ == "__main__":
    unittest.main()
