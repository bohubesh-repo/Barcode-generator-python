# Simple Python Barcode System

Lightweight local tool with only two modules:
- **Generate Barcode**
- **Scan Barcode**

Uses **CSV files only** (no SQL).

## Files

- `app.py`
- `product_types.csv`
- `color_codes.csv`
- `size_codes.csv`
- `model_codes.csv`
- `manufacturer_codes.csv`
- `database.csv` (main lookup database for scans)
- `templates/` and `static/`

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: `http://localhost:5000`

## Barcode format

`[SKU]-[ENC_BATCH]-[SERIAL]`

Example:
`FKJS-01-BLK-M-X7K9P2-0045`

Where:
- SKU: `ProductCode-Model-Color-Size`
- ENC_BATCH: deterministic hash of `Location|ShopName|Date` (`sha256` + base36)
- SERIAL: 4-digit serial (`0001` ...)
