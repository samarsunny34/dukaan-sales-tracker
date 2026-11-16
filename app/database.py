"""SQLite backend for Dukaan Sales Tracker.

Tables
------
products: id, name, category, price (PKR), stock, low_stock_at, created_at
sales:    id, customer_name, product_id, quantity, unit_price, total,
          payment_method, sale_date (YYYY-MM-DD HH:MM), notes

A sale always decrements stock. Deleting a sale restores it.
All money is in PKR. No network is needed - the database lives on the phone.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL DEFAULT 'General',
    price REAL NOT NULL CHECK (price >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    low_stock_at INTEGER NOT NULL DEFAULT 5,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL DEFAULT 'Walk-in Customer',
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    total REAL NOT NULL CHECK (total >= 0),
    payment_method TEXT NOT NULL DEFAULT 'Cash',
    sale_date TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(product_id);
"""

PAYMENT_METHODS = ["Cash", "JazzCash", "EasyPaisa", "Bank Transfer", "Credit (Udhar)"]
CATEGORIES = ["Grocery", "Dairy", "Bakery", "Beverages", "Personal Care",
              "Household", "Snacks", "Other"]


class Store:
    """All database access goes through here, so the UI never writes SQL."""

    def __init__(self, db_path: str | Path = "dukaan.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self):
        self.conn.close()

    # -- products ---------------------------------------------------------
    def add_product(self, name, category, price, stock, low_stock_at=5):
        name = name.strip()
        if not name:
            raise ValueError("Product name is required.")
        if price < 0 or stock < 0:
            raise ValueError("Price and stock cannot be negative.")
        cur = self.conn.execute(
            "INSERT INTO products (name, category, price, stock, low_stock_at, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (name, category, float(price), int(stock), int(low_stock_at),
             datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_product(self, product_id, name, category, price, stock, low_stock_at=5):
        if price < 0 or stock < 0:
            raise ValueError("Price and stock cannot be negative.")
        cur = self.conn.execute(
            "UPDATE products SET name=?, category=?, price=?, stock=?, low_stock_at=?"
            " WHERE id=?",
            (name.strip(), category, float(price), int(stock), int(low_stock_at), product_id),
        )
        self.conn.commit()
        return cur.rowcount

    def delete_product(self, product_id):
        cur = self.conn.execute("DELETE FROM products WHERE id=?", (product_id,))
        self.conn.commit()
        return cur.rowcount

    def list_products(self, search=""):
        if search.strip():
            like = f"%{search.strip()}%"
            rows = self.conn.execute(
                "SELECT * FROM products WHERE name LIKE ? OR category LIKE ?"
                " ORDER BY name", (like, like))
        else:
            rows = self.conn.execute("SELECT * FROM products ORDER BY name")
        return [dict(r) for r in rows]

    def get_product(self, product_id):
        row = self.conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        return dict(row) if row else None

    def low_stock(self):
        rows = self.conn.execute(
            "SELECT * FROM products WHERE stock <= low_stock_at ORDER BY stock, name")
        return [dict(r) for r in rows]

    # -- sales ------------------------------------------------------------
    def add_sale(self, customer_name, product_id, quantity,
                 payment_method="Cash", notes="", sale_date=None):
        product = self.get_product(product_id)
        if product is None:
            raise ValueError("Product not found.")
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError("Quantity must be at least 1.")
        if quantity > product["stock"]:
            raise ValueError(
                f"Not enough stock for {product['name']}: only {product['stock']} left.")
        unit_price = float(product["price"])
        total = round(unit_price * quantity, 2)
        when = sale_date or datetime.now().strftime("%Y-%m-%d %H:%M")
        cur = self.conn.execute(
            "INSERT INTO sales (customer_name, product_id, quantity, unit_price,"
            " total, payment_method, sale_date, notes)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (customer_name.strip() or "Walk-in Customer", product_id, quantity,
             unit_price, total, payment_method, when, notes.strip()),
        )
        self.conn.execute(
            "UPDATE products SET stock = stock - ? WHERE id=?", (quantity, product_id))
        self.conn.commit()
        return cur.lastrowid, total

    def delete_sale(self, sale_id):
        row = self.conn.execute("SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
        if row is None:
            return 0
        self.conn.execute("DELETE FROM sales WHERE id=?", (sale_id,))
        # Restore the stock that this sale had used.
        self.conn.execute(
            "UPDATE products SET stock = stock + ? WHERE id=?",
            (row["quantity"], row["product_id"]))
        self.conn.commit()
        return 1

    def list_sales(self, search="", limit=200):
        sql = ("SELECT s.*, p.name AS product_name FROM sales s"
               " JOIN products p ON p.id = s.product_id")
        params: list = []
        if search.strip():
            sql += " WHERE s.customer_name LIKE ? OR p.name LIKE ?"
            params += [f"%{search.strip()}%", f"%{search.strip()}%"]
        sql += " ORDER BY s.sale_date DESC, s.id DESC LIMIT ?"
        params.append(limit)
        return [dict(r) for r in self.conn.execute(sql, params)]

    # -- dashboard --------------------------------------------------------
    def summary(self, day=None):
        day = day or datetime.now().strftime("%Y-%m-%d")
        row = self.conn.execute(
            "SELECT COUNT(*) AS orders, COALESCE(SUM(total), 0) AS revenue,"
            " COALESCE(SUM(quantity), 0) AS items FROM sales WHERE date(sale_date) = ?",
            (day,)).fetchone()
        return {"date": day, "orders": row["orders"],
                "revenue": round(row["revenue"], 2), "items": row["items"]}

    def top_products(self, limit=5):
        rows = self.conn.execute(
            "SELECT p.name, SUM(s.quantity) AS qty, SUM(s.total) AS revenue"
            " FROM sales s JOIN products p ON p.id = s.product_id"
            " GROUP BY p.id, p.name ORDER BY revenue DESC LIMIT ?", (limit,))
        return [dict(r) for r in rows]

    def sales_by_day(self, days=7):
        rows = self.conn.execute(
            "SELECT date(sale_date) AS day, SUM(total) AS revenue"
            " FROM sales GROUP BY day ORDER BY day DESC LIMIT ?", (days,))
        return [dict(r) for r in reversed(rows)]

    def totals(self):
        row = self.conn.execute(
            "SELECT COUNT(*) AS products, COALESCE(SUM(stock), 0) AS stock"
            " FROM products").fetchone()
        sales = self.conn.execute(
            "SELECT COUNT(*) AS orders, COALESCE(SUM(total), 0) AS revenue FROM sales"
            ).fetchone()
        return {"products": row["products"], "stock": row["stock"],
                "orders": sales["orders"], "revenue": round(sales["revenue"], 2)}
