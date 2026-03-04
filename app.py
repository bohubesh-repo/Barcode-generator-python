from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path
from typing import Dict, List

import base36
from barcode import Code128
from barcode.writer import ImageWriter
from flask import Flask, jsonify, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.csv"
BARCODE_DIR = BASE_DIR / "static" / "barcodes"

FIELDNAMES = [
    "FullBarcode",
    "SKU",
    "ENC_BATCH",
    "Serial",
    "RawBatch",
    "Category",
    "Subcategory",
    "Model",
    "Color",
    "Size",
    "Status",
]

app = Flask(__name__)


def ensure_storage() -> None:
    BARCODE_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        with DB_PATH.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writeheader()


def encode_batch(raw_batch: str) -> str:
    digest = hashlib.sha256(raw_batch.encode("utf-8")).hexdigest()
    encoded = base36.dumps(int(digest, 16)).upper()
    return encoded[:6].rjust(6, "0")


def read_rows() -> List[Dict[str, str]]:
    ensure_storage()
    with DB_PATH.open("r", newline="", encoding="utf-8") as csvfile:
        return list(csv.DictReader(csvfile))


def append_rows(rows: List[Dict[str, str]]) -> None:
    ensure_storage()
    existing = {row["FullBarcode"] for row in read_rows()}
    with DB_PATH.open("a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        for row in rows:
            full_barcode = row["FullBarcode"]
            if full_barcode in existing:
                continue
            writer.writerow(row)
            existing.add(full_barcode)


def build_records(form_data: Dict[str, str]) -> List[Dict[str, str]]:
    sku = form_data["sku"].strip()
    raw_batch = form_data["raw_batch"].strip()
    quantity = max(1, int(form_data["quantity"]))

    enc_batch = encode_batch(raw_batch)
    records: List[Dict[str, str]] = []

    for serial_number in range(1, quantity + 1):
        serial = f"{serial_number:04d}"
        full_barcode = f"{sku}-{enc_batch}-{serial}"

        barcode_file = BARCODE_DIR / full_barcode
        if not (barcode_file.with_suffix(".png")).exists():
            generator = Code128(full_barcode, writer=ImageWriter())
            generator.save(str(barcode_file))

        records.append(
            {
                "FullBarcode": full_barcode,
                "SKU": sku,
                "ENC_BATCH": enc_batch,
                "Serial": serial,
                "RawBatch": raw_batch,
                "Category": form_data["category"].strip(),
                "Subcategory": form_data["subcategory"].strip(),
                "Model": form_data["model"].strip(),
                "Color": form_data["color"].strip(),
                "Size": form_data["size"].strip(),
                "Status": "In Stock",
            }
        )

    return records


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["GET", "POST"])
def generate():
    generated_rows: List[Dict[str, str]] = []

    if request.method == "POST":
        records = build_records(request.form)
        append_rows(records)
        generated_rows = records

    return render_template("generate.html", generated_rows=generated_rows)


@app.route("/scan")
def scan():
    return render_template("scan.html")


@app.route("/api/lookup")
def lookup_barcode():
    value = request.args.get("value", "").strip()
    if not value:
        return jsonify({"found": False, "message": "Barcode is required."}), 400

    for row in read_rows():
        if row["FullBarcode"] == value:
            return jsonify({"found": True, "record": row})

    return jsonify({"found": False, "message": "No record found for this barcode."}), 404


if __name__ == "__main__":
    ensure_storage()
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    app.run(host=host, port=port, debug=False)
