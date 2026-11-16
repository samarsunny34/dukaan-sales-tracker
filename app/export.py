"""Export sales to CSV, ready to open in Excel or load into Power BI."""
from __future__ import annotations

import csv
from pathlib import Path


def export_sales_csv(store, path: str | Path) -> Path:
    path = Path(path)
    rows = store.list_sales(limit=100000)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sale_id", "date", "customer", "product", "quantity",
                    "unit_price_pkr", "total_pkr", "payment_method", "notes"])
        for r in rows:
            w.writerow([r["id"], r["sale_date"], r["customer_name"], r["product_name"],
                        r["quantity"], r["unit_price"], r["total"],
                        r["payment_method"], r["notes"]])
    return path
