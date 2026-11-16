"""Backend tests - run with: python -m unittest discover -s tests -v"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import Store  # noqa: E402
from app.export import export_sales_csv  # noqa: E402
from app.seed import seed_if_empty  # noqa: E402


class TestStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(os.path.join(self.tmp.name, "test.db"))

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_seed_adds_products(self):
        self.assertEqual(seed_if_empty(self.store), 12)
        self.assertEqual(seed_if_empty(self.store), 0)  # second run adds nothing

    def test_sale_reduces_stock_and_totals(self):
        pid = self.store.add_product("Test Tea", "Beverages", 100, 10)
        _id, total = self.store.add_sale("Ayesha", pid, 3)
        self.assertEqual(total, 300)
        self.assertEqual(self.store.get_product(pid)["stock"], 7)
        self.assertEqual(self.store.summary()["revenue"], 300)

    def test_sale_blocked_when_out_of_stock(self):
        pid = self.store.add_product("Test Tea", "Beverages", 100, 1)
        with self.assertRaises(ValueError):
            self.store.add_sale("Bilal", pid, 5)

    def test_delete_sale_restores_stock(self):
        pid = self.store.add_product("Test Tea", "Beverages", 100, 10)
        sale_id, _ = self.store.add_sale("Ayesha", pid, 2)
        self.store.delete_sale(sale_id)
        self.assertEqual(self.store.get_product(pid)["stock"], 10)

    def test_low_stock_and_top_products(self):
        pid = self.store.add_product("Low Item", "Other", 50, 2, low_stock_at=5)
        self.assertEqual(len(self.store.low_stock()), 1)
        self.store.add_sale("Ayesha", pid, 1)
        self.assertEqual(self.store.top_products()[0]["name"], "Low Item")

    def test_export_csv(self):
        pid = self.store.add_product("Test Tea", "Beverages", 100, 10)
        self.store.add_sale("Ayesha", pid, 2)
        path = export_sales_csv(self.store, os.path.join(self.tmp.name, "out.csv"))
        text = path.read_text(encoding="utf-8")
        self.assertIn("sale_id,date,customer,product", text)
        self.assertIn("Ayesha", text)
        self.assertIn("200", text)


if __name__ == "__main__":
    unittest.main()
