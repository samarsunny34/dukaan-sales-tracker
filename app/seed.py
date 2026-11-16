"""Seed the store with sample Pakistani shop products (run once, from main)."""
from __future__ import annotations

SAMPLE_PRODUCTS = [
    ("Atta 10kg", "Grocery", 1250, 20, 5),
    ("Sugar 1kg", "Grocery", 180, 40, 10),
    ("Basmati Rice 1kg", "Grocery", 420, 25, 5),
    ("Cooking Oil 1L", "Grocery", 650, 15, 5),
    ("Tea 500g", "Beverages", 950, 18, 5),
    ("Milk 1L", "Dairy", 260, 30, 10),
    ("Bread", "Bakery", 120, 25, 5),
    ("Bath Soap", "Personal Care", 150, 50, 10),
    ("Shampoo 200ml", "Personal Care", 480, 12, 5),
    ("Washing Powder 1kg", "Household", 380, 20, 5),
    ("Biscuits Pack", "Snacks", 90, 60, 10),
    ("Cold Drink 1.5L", "Beverages", 220, 24, 5),
]


def seed_if_empty(store) -> int:
    """Add sample products only when the product list is empty. Returns count added."""
    if store.list_products():
        return 0
    for name, category, price, stock, low in SAMPLE_PRODUCTS:
        store.add_product(name, category, price, stock, low)
    return len(SAMPLE_PRODUCTS)
