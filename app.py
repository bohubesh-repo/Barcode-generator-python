from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path
from threading import Lock
from typing import Dict, List

from barcode import Code128
from barcode.writer import ImageWriter
from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.csv"
BARCODE_DIR = BASE_DIR / "static" / "barcodes"

PRODUCT_TYPES_PATH = BASE_DIR / "product_types.csv"
COLOR_CODES_PATH = BASE_DIR / "color_codes.csv"
SIZE_CODES_PATH = BASE_DIR / "size_codes.csv"
MODEL_CODES_PATH = BASE_DIR / "model_codes.csv"
MANUFACTURER_CODES_PATH = BASE_DIR / "manufacturer_codes.csv"

DB_FIELDS = [
    "FullBarcode",
    "SKU",
    "ENC_BATCH",
    "Serial",
    "RawBatch",
    "ProductCode",
    "Model",
    "Color",
    "Size",
]

CSV_LOCK = Lock()
app = Flask(__name__)


def base36_encode(number: int) -> str:
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if number == 0:
        return "0"

    value = number
    result = []
    while value:
        value, remainder = divmod(value, 36)
        result.append(alphabet[remainder])
    return "".join(reversed(result))


def ensure_storage() -> None:
    BARCODE_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        with DB_PATH.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=DB_FIELDS)
            writer.writeheader()


def encode_batch(raw_batch: str) -> str:
    digest_hex = hashlib.sha256(raw_batch.encode("utf-8")).hexdigest()
    digest_int = int(digest_hex, 16)
    encoded = base36_encode(digest_int)
    return encoded[:6].rjust(6, "0")


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as csvfile:
        return list(csv.DictReader(csvfile))


def read_database_rows() -> List[Dict[str, str]]:
    ensure_storage()
    with DB_PATH.open("r", newline="", encoding="utf-8") as csvfile:
        return list(csv.DictReader(csvfile))


def append_database_rows(rows: List[Dict[str, str]]) -> int:
    ensure_storage()
    with CSV_LOCK:
        existing = {row["FullBarcode"] for row in read_database_rows()}
        inserted = 0
        with DB_PATH.open("a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=DB_FIELDS)
            for row in rows:
                barcode_value = row["FullBarcode"]
                if barcode_value in existing:
                    continue
                writer.writerow(row)
                existing.add(barcode_value)
                inserted += 1
    return inserted


def generate_records(form_data: Dict[str, str]) -> List[Dict[str, str]]:
    product_code = form_data["product_code"].strip().upper()
    model = form_data["model"].strip().upper()
    color = form_data["color"].strip().upper()
    size = form_data["size"].strip().upper()
    quantity = max(1, int(form_data["quantity"]))

    location = form_data["location"].strip()
    shop_name = form_data["shop_name"].strip()
    date_code = form_data["date_code"].strip()
    raw_batch = f"{location}|{shop_name}|{date_code}"

    sku = f"{product_code}-{model}-{color}-{size}"
    enc_batch = encode_batch(raw_batch)

    records = []
    for serial_number in range(1, quantity + 1):
        serial = f"{serial_number:04d}"
        full_barcode = f"{sku}-{enc_batch}-{serial}"

        barcode_file = BARCODE_DIR / full_barcode
        if not barcode_file.with_suffix(".png").exists():
            code = Code128(full_barcode, writer=ImageWriter())
            code.save(str(barcode_file))

        records.append(
            {
                "FullBarcode": full_barcode,
                "SKU": sku,
                "ENC_BATCH": enc_batch,
                "Serial": serial,
                "RawBatch": raw_batch,
                "ProductCode": product_code,
                "Model": model,
                "Color": color,
                "Size": size,
            }
        )

    return records


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/generate", methods=["GET", "POST"])
def generate() -> str:
    inserted_count = 0
    generated_rows: List[Dict[str, str]] = []

    if request.method == "POST":
        generated_rows = generate_records(request.form)
        inserted_count = append_database_rows(generated_rows)

    return render_template(
        "generate.html",
        product_types=read_csv_rows(PRODUCT_TYPES_PATH),
        color_codes=read_csv_rows(COLOR_CODES_PATH),
        size_codes=read_csv_rows(SIZE_CODES_PATH),
        model_codes=read_csv_rows(MODEL_CODES_PATH),
        manufacturer_codes=read_csv_rows(MANUFACTURER_CODES_PATH),
        generated_rows=generated_rows,
        inserted_count=inserted_count,
    )


@app.route("/scan")
def scan() -> str:
    return render_template("scan.html")


@app.route("/api/lookup")
def lookup():
    barcode_value = request.args.get("value", "").strip()
    if not barcode_value:
        return jsonify({"found": False, "message": "Barcode is required."}), 400

    for row in read_database_rows():
        if row["FullBarcode"] == barcode_value:
            return jsonify({"found": True, "record": row})

    return jsonify({"found": False, "message": "No matching barcode found."}), 404


if __name__ == "__main__":
    ensure_storage()
    app.run(host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "5000")))
