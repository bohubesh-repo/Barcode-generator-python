# Simple Python Barcode Tool

Lightweight local barcode web app with:
- Barcode generation (Code128 PNG)
- Barcode scanning (camera + manual fallback)
- CSV storage only (`database.csv`)

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: `http://localhost:5000`

## Project structure

- `app.py` – Flask backend and CSV logic
- `database.csv` – single CSV database
- `templates/` – pages (`index`, `generate`, `scan`)
- `static/barcodes/` – generated PNG files
- `static/scanner.js` – scanner + lookup logic
