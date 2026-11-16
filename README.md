# Dukaan Sales Tracker

An Android sales app for a small shop, built in **Python with Flet**.
Add a sale in 10 seconds, see today's revenue, track stock, and export
sales to CSV for Excel or Power BI.

## What it does

| Screen | Features |
| --- | --- |
| **Dashboard** | Today's revenue, orders, items sold, last-7-days chart, top products, low-stock alerts |
| **New Sale** | Pick a product, quantity, customer, payment method (Cash / JazzCash / EasyPaisa / Bank / Credit). Total is calculated live. Stock is reduced automatically, and a sale is blocked if there is not enough stock. |
| **Products** | Add products (name, category, price, stock), search, delete |
| **Sales** | Full sales history, search by customer or product, delete a sale (stock is restored), **Export CSV for Power BI** |

## Tech stack

- **Frontend:** Flet (Python UI, runs on Android, Windows, web)
- **Backend:** SQLite, on the phone — works fully offline, no server needed
- **Data:** `app/database.py` — products, sales, stock, summaries
- **Export:** `app/export.py` — CSV with `sale_id, date, customer, product, quantity, unit_price_pkr, total_pkr, payment_method, notes`

## Project structure

```
dukaan-sales-tracker/
├── main.py                 # Flet UI - all 4 screens
├── app/
│   ├── database.py         # SQLite backend (Store class)
│   ├── export.py           # CSV export for Power BI
│   └── seed.py             # 12 sample Pakistani shop products
├── tests/
│   └── test_database.py    # backend tests
├── requirements.txt
└── BUILD_ANDROID.md        # how to build the APK
```

## Run on your computer (test it first)

```bash
pip install -r requirements.txt
python main.py
```

The app opens in a window with 12 sample products already loaded, so you
can add a sale straight away and see the dashboard update.

## Build the Android APK

See [BUILD_ANDROID.md](BUILD_ANDROID.md). In short:

```bash
flet build apk
```

The APK is created under `build/apk/`. Copy it to your phone and install it.

### Build it on GitHub (no local setup needed)

Every push to `main` also builds the APK automatically with GitHub
Actions (`.github/workflows/build-apk.yml`). Open the repo's **Actions**
tab, click the latest **Build APK** run, and download the
**dukaan-sales-tracker-apk** artifact — it contains the ready-to-install
`.apk` file.

## Run the tests

```bash
python -m unittest discover -s tests -v
```

## Roadmap

- [ ] Barcode scanning for products
- [ ] Monthly profit report (sale price vs. cost price)
- [ ] Customer credit / udhar ledger
- [ ] Cloud backup (optional, with a small FastAPI backend)
