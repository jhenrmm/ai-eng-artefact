import csv
import json
from pathlib import Path

import pymupdf

from config import CHUNK_SIZE, DATA_DIR
from .embedding import embed


def read_pdf_text(pdf_path):
    with pymupdf.open(pdf_path) as document:
        return "\n".join(page.get_text() for page in document)


def split_text(text, size=CHUNK_SIZE):
    return [
        text[index:index + size]
        for index in range(0, len(text), size)
        if text[index:index + size].strip()
    ]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def load_tables(csv_dir):
    tables = {}
    for path in sorted(Path(csv_dir).glob("*.csv")):
        table_name = path.stem.split(" - ")[-1]
        tables[table_name] = read_csv(path)
    return tables


def index_by(rows, key):
    return {row[key]: row for row in rows}


def format_brl(value):
    if value in (None, ""):
        return "unknown"
    try:
        return f"R$ {float(value):.2f}"
    except (TypeError, ValueError):
        return f"R$ {value}"


def format_category(row):
    return (
        f"[categories] Category {row['category_id']}: {row['name']}. "
        f"{row['description']}."
    )


def format_product(row, categories):
    try:
        specs = json.loads(row.get("specs") or "{}")
    except json.JSONDecodeError:
        specs = {}
    specs_text = "; ".join(f"{key}={value}" for key, value in specs.items())
    category = categories.get(row["category_id"], {}).get("name", "unknown")
    return (
        f"[products] Product {row['product_id']}: {row['name']}. "
        f"Category: {category}. Price: {format_brl(row['price_brl'])}. "
        f"Stock: {row['stock_quantity']}. Status: {row['status']}. "
        f"Description: {row['description']} "
        f"Specs: {specs_text or 'none'}."
    )


def format_order(row, customers):
    customer = customers.get(row["customer_id"], {})
    return (
        f"[orders] Order {row['order_id']}: customer {customer.get('name', 'unknown')} "
        f"(id {row['customer_id']}). Date: {row['order_date']}. Status: {row['status']}. "
        f"Total: {format_brl(row['total_brl'])}. Payment: {row['payment_method']}. "
        f"Tracking: {row['tracking_code']}. Estimated delivery: {row['estimated_delivery']}. "
        f"Notes: {row['notes'] or 'none'}."
    )


def format_order_item(row, orders, products):
    order = orders.get(row["order_id"], {})
    product = products.get(row["product_id"], {})
    quantity = int(row["quantity"])
    unit_price = product.get("price_brl")
    line_total = format_brl(float(unit_price) * quantity) if unit_price else "unknown"
    return (
        f"[order_items] Order {row['order_id']} includes {quantity} unit(s) of product "
        f"{row['product_id']} ({product.get('name', 'unknown')}). "
        f"Unit price: {format_brl(unit_price)}. Line total: {line_total}. "
        f"Order status: {order.get('status', 'unknown')}."
    )


def format_promotion(row, products):
    product = products.get(row["product_id"], {})
    active = "yes" if row["is_active"] == "1" else "no"
    return (
        f"[promotions] Promotion {row['promotion_id']}: {row['discount_percent']}% off "
        f"product {row['product_id']} ({product.get('name', 'unknown')}). "
        f"Description: {row['description']}. Active: {active}."
    )


def build_csv_chunks(csv_dir):
    tables = load_tables(csv_dir)
    categories = index_by(tables.get("categories", []), "category_id")
    products = index_by(tables.get("products", []), "product_id")
    customers = index_by(tables.get("customers", []), "customer_id")
    orders = index_by(tables.get("orders", []), "order_id")

    chunks = []
    chunks.extend(format_product(row, categories) for row in products.values())
    chunks.extend(format_category(row) for row in categories.values())
    chunks.extend(format_order(row, customers) for row in orders.values())
    chunks.extend(
        format_order_item(row, orders, products)
        for row in tables.get("order_items", [])
    )
    chunks.extend(
        format_promotion(row, products)
        for row in tables.get("promotions", [])
    )
    return chunks


def ingest(pdf_path, csv_dir=DATA_DIR):
    text = read_pdf_text(pdf_path)
    chunks = split_text(text)
    chunks.extend(build_csv_chunks(csv_dir))
    embeddings = embed(chunks)
    return chunks, embeddings
