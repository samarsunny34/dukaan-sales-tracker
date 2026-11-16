"""Dukaan Sales Tracker - Android app in Python (Flet).

Frontend + backend in one app:
  * Frontend: Flet UI - Dashboard, New Sale, Products, Sales History
  * Backend:  SQLite (app/database.py) - products, sales, stock, summaries
  * Export:   CSV for Excel / Power BI (app/export.py)

Run on desktop for testing:
    pip install -r requirements.txt
    python main.py

Build the Android APK (needs Flutter SDK + Android SDK, see BUILD_ANDROID.md):
    flet build apk
"""
from __future__ import annotations

import flet as ft

from app.database import CATEGORIES, PAYMENT_METHODS, Store
from app.export import export_sales_csv
from app.seed import seed_if_empty


def money(amount) -> str:
    return f"Rs {amount:,.0f}"


class App:
    def __init__(self, page: ft.Page):
        self.page = page
        self.store = Store("dukaan.db")
        seed_if_empty(self.store)
        self.view = "dashboard"
        self.search_products = ""
        self.search_sales = ""

        page.title = "Dukaan Sales Tracker"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.window_width = 480
        page.window_height = 860

        self.content = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        self.rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=72,
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.DASHBOARD, label="Home"),
                ft.NavigationRailDestination(icon=ft.Icons.ADD_SHOPPING_CART, label="New Sale"),
                ft.NavigationRailDestination(icon=ft.Icons.INVENTORY_2, label="Products"),
                ft.NavigationRailDestination(icon=ft.Icons.RECEIPT_LONG, label="Sales"),
            ],
            on_change=self._on_nav,
        )
        page.add(ft.Row([self.rail, ft.VerticalDivider(width=1), self.content], expand=True))
        self.refresh()

    # -- helpers ----------------------------------------------------------
    def snack(self, message: str):
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()

    def _on_nav(self, e):
        self.view = ["dashboard", "sale", "products", "sales"][e.control.selected_index]
        self.refresh()

    def refresh(self):
        builders = {
            "dashboard": self._dashboard,
            "sale": self._sale_form,
            "products": self._products,
            "sales": self._sales,
        }
        self.content.controls = builders[self.view]()
        self.page.update()

    @staticmethod
    def _card(title: str, value: str, icon: str) -> ft.Control:
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [ft.Icon(icon, size=28), ft.Text(title, size=12),
                     ft.Text(value, size=18, weight=ft.FontWeight.BOLD)],
                    spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=12, width=150),
        )

    # -- dashboard --------------------------------------------------------
    def _dashboard(self):
        today = self.store.summary()
        totals = self.store.totals()
        low = self.store.low_stock()
        top = self.store.top_products()
        days = self.store.sales_by_day(7)
        max_day = max([d["revenue"] for d in days], default=1) or 1

        controls = [
            ft.Text("Dashboard", size=24, weight=ft.FontWeight.BOLD),
            ft.Text(f"Today: {today['date']}  •  {today['orders']} orders",
                    size=13, color="grey"),
            ft.Row([
                self._card("Today's Sales", money(today["revenue"]), ft.Icons.TODAY),
                self._card("Items Sold", str(today["items"]), ft.Icons.SHOPPING_BAG),
            ], wrap=True),
            ft.Row([
                self._card("Total Revenue", money(totals["revenue"]), ft.Icons.ACCOUNT_BALANCE_WALLET),
                self._card("Products", str(totals["products"]), ft.Icons.INVENTORY_2),
            ], wrap=True),
            ft.Text("Last 7 days", size=16, weight=ft.FontWeight.BOLD),
        ]
        for d in days:
            width = max(8, int(220 * d["revenue"] / max_day))
            controls.append(ft.Row([
                ft.Text(d["day"], size=12, width=90),
                ft.Container(width=width, height=14, bgcolor="blue", border_radius=4),
                ft.Text(money(d["revenue"]), size=12),
            ]))
        controls.append(ft.Text("Top products", size=16, weight=ft.FontWeight.BOLD))
        for p in top or [{"name": "No sales yet", "qty": 0, "revenue": 0}]:
            controls.append(ft.Text(f"{p['name']} — {p['qty']} sold — {money(p['revenue'])}"))
        controls.append(ft.Text("Low stock — order soon", size=16, weight=ft.FontWeight.BOLD))
        for p in low:
            controls.append(ft.Text(f"⚠ {p['name']}: {p['stock']} left",
                                    color="red"))
        if not low:
            controls.append(ft.Text("All stock levels are OK."))
        return controls

    # -- new sale ---------------------------------------------------------
    def _sale_form(self):
        products = self.store.list_products()
        self._product_dd = ft.Dropdown(
            label="Product", width=320,
            options=[ft.dropdown.Option(str(p["id"]), f"{p['name']} — {money(p['price'])} (stock {p['stock']})")
                     for p in products])
        self._qty = ft.TextField(label="Quantity", value="1", width=320,
                                 keyboard_type=ft.KeyboardType.NUMBER)
        self._customer = ft.TextField(label="Customer name (optional)", width=320)
        self._payment = ft.Dropdown(
            label="Payment", width=320, value="Cash",
            options=[ft.dropdown.Option(m) for m in PAYMENT_METHODS])
        self._notes = ft.TextField(label="Notes (optional)", width=320)
        self._total = ft.Text("Total: —", size=16, weight=ft.FontWeight.BOLD)

        def update_total(_e=None):
            try:
                p = self.store.get_product(int(self._product_dd.value))
                qty = int(self._qty.value or 0)
                self._total.value = f"Total: {money(p['price'] * qty)}" if p else "Total: —"
            except (TypeError, ValueError):
                self._total.value = "Total: —"
            self.page.update()

        self._product_dd.on_change = update_total
        self._qty.on_change = update_total

        def save_sale(_e):
            try:
                if not self._product_dd.value:
                    raise ValueError("Please choose a product.")
                _id, total = self.store.add_sale(
                    self._customer.value or "Walk-in Customer",
                    int(self._product_dd.value), int(self._qty.value),
                    self._payment.value or "Cash", self._notes.value or "")
                self.snack(f"Sale saved: {money(total)}")
                self.view = "dashboard"
                self.refresh()
            except (ValueError, TypeError) as exc:
                self.snack(str(exc))

        return [
            ft.Text("New Sale", size=24, weight=ft.FontWeight.BOLD),
            self._product_dd, self._qty, self._customer, self._payment, self._notes,
            self._total,
            ft.ElevatedButton("Save Sale", icon=ft.Icons.CHECK, on_click=save_sale),
            ft.Text("Stock is reduced automatically. If stock is too low, the sale is blocked.",
                    size=12, color="grey"),
        ]

    # -- products ---------------------------------------------------------
    def _products(self):
        def add_product(_e):
            try:
                price = float(self._p_price.value)
                stock = int(self._p_stock.value)
                self.store.add_product(self._p_name.value, self._p_cat.value or "General",
                                       price, stock)
                self.snack(f"Added {self._p_name.value}")
                self.refresh()
            except (ValueError, TypeError) as exc:
                self.snack(str(exc) or "Check price / stock — numbers only.")

        self._p_name = ft.TextField(label="Product name", width=320)
        self._p_cat = ft.Dropdown(label="Category", width=320, value="Grocery",
                                  options=[ft.dropdown.Option(c) for c in CATEGORIES])
        self._p_price = ft.TextField(label="Price (PKR)", width=150,
                                     keyboard_type=ft.KeyboardType.NUMBER)
        self._p_stock = ft.TextField(label="Stock", width=150,
                                     keyboard_type=ft.KeyboardType.NUMBER)
        search = ft.TextField(label="Search products", width=320, value=self.search_products,
                              on_change=lambda e: self._set_search("products", e.control.value))

        rows = []
        for p in self.store.list_products(self.search_products):
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(p["name"])),
                ft.DataCell(ft.Text(money(p["price"]))),
                ft.DataCell(ft.Text(str(p["stock"]))),
                ft.DataCell(ft.IconButton(
                    icon=ft.Icons.DELETE, tooltip="Delete",
                    on_click=lambda e, pid=p["id"]: self._delete_product(pid))),
            ]))
        return [
            ft.Text("Products", size=24, weight=ft.FontWeight.BOLD),
            self._p_name, self._p_cat,
            ft.Row([self._p_price, self._p_stock]),
            ft.ElevatedButton("Add Product", icon=ft.Icons.ADD, on_click=add_product),
            search,
            ft.DataTable(columns=[
                ft.DataColumn(ft.Text("Product")), ft.DataColumn(ft.Text("Price")),
                ft.DataColumn(ft.Text("Stock")), ft.DataColumn(ft.Text("")),
            ], rows=rows) if rows else ft.Text("No products match."),
        ]

    def _delete_product(self, product_id):
        try:
            self.store.delete_product(product_id)
            self.snack("Product deleted.")
        except Exception as exc:  # e.g. product still has sales linked to it
            self.snack(f"Cannot delete: {exc}")
        self.refresh()

    def _set_search(self, kind, value):
        if kind == "products":
            self.search_products = value
        else:
            self.search_sales = value
        self.refresh()

    # -- sales history ----------------------------------------------------
    def _sales(self):
        search = ft.TextField(label="Search by customer or product", width=320,
                              value=self.search_sales,
                              on_change=lambda e: self._set_search("sales", e.control.value))

        def export(_e):
            path = export_sales_csv(self.store, "sales_export.csv")
            self.snack(f"Exported {len(self.store.list_sales())} sales to {path}")

        rows = []
        for s in self.store.list_sales(self.search_sales):
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(s["sale_date"][:10])),
                ft.DataCell(ft.Text(s["product_name"])),
                ft.DataCell(ft.Text(str(s["quantity"]))),
                ft.DataCell(ft.Text(money(s["total"]))),
                ft.DataCell(ft.IconButton(
                    icon=ft.Icons.DELETE, tooltip="Delete (restores stock)",
                    on_click=lambda e, sid=s["id"]: self._delete_sale(sid))),
            ]))
        return [
            ft.Text("Sales History", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([ft.ElevatedButton("Export CSV for Power BI", icon=ft.Icons.DOWNLOAD,
                                      on_click=export)]),
            search,
            ft.DataTable(columns=[
                ft.DataColumn(ft.Text("Date")), ft.DataColumn(ft.Text("Product")),
                ft.DataColumn(ft.Text("Qty")), ft.DataColumn(ft.Text("Total")),
                ft.DataColumn(ft.Text("")),
            ], rows=rows) if rows else ft.Text("No sales yet — add your first sale."),
        ]

    def _delete_sale(self, sale_id):
        self.store.delete_sale(sale_id)
        self.snack("Sale deleted — stock restored.")
        self.refresh()


def main(page: ft.Page):
    App(page)


if __name__ == "__main__":
    ft.app(target=main)
