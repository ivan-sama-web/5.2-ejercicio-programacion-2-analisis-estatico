#!/usr/bin/env python3
"""Compute total sales from a product catalogue and sales record.

Usage:
    python computeSales.py priceCatalogue.json salesRecord.json
    python computeSales.py priceCatalogue.json salesRecord.json --total
    python computeSales.py priceCatalogue.json salesRecord.json --detail

Flags:
    --total   Show only the grand total (default).
    --detail  Show the full detailed report.

This program reads a JSON product catalogue and a JSON sales record,
computes the total cost per sale and overall, then outputs results
to the screen and to SalesResults.txt.

Author: Ivan Troy Santaella Martinez
"""

import argparse
import json
import sys
import time


def load_json(filepath):
    """Load and parse a JSON file, returning the parsed data.

    Args:
        filepath: Path to the JSON file.

    Returns:
        Parsed JSON data (list or dict).

    Raises:
        SystemExit: If file cannot be read or parsed.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"Error: File '{filepath}' contains invalid JSON: {exc}")
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied reading '{filepath}'.")
        sys.exit(1)
    except OSError as exc:
        print(f"Error: Could not read '{filepath}': {exc}")
        sys.exit(1)
    return data


def build_price_catalogue(products):
    """Build a dictionary mapping product title to price.

    Args:
        products: List of product dictionaries from the catalogue.

    Returns:
        Dict mapping product title (str) to price (float).
    """
    catalogue = {}
    for idx, product in enumerate(products):
        title = product.get("title")
        price = product.get("price")

        if not title:
            print(f"Warning: Product at index {idx} has no title, skipping.")
            continue

        if price is None:
            print(f"Warning: Product '{title}' has no price, skipping.")
            continue

        try:
            price = float(price)
        except (ValueError, TypeError):
            print(f"Warning: Product '{title}' has invalid price "
                  f"'{price}', skipping.")
            continue

        if price < 0:
            print(f"Warning: Product '{title}' has negative price, skipping.")
            continue

        catalogue[title] = price
    return catalogue


def compute_sales(catalogue, sales_records):
    """Compute totals for each sale and grand total.

    Args:
        catalogue: Dict mapping product title to price.
        sales_records: List of sale line-item dictionaries.

    Returns:
        Tuple of (sale_totals, grand_total) where sale_totals is a
        dict mapping SALE_ID to a dict with 'date', 'items' list,
        and 'total'.
    """
    sale_totals = {}
    grand_total = 0.0

    for idx, record in enumerate(sales_records):
        sale_id = record.get("SALE_ID")
        if sale_id is None:
            print(f"Warning: Record at index {idx} has no SALE_ID, skipping.")
            continue

        product = record.get("Product")
        if not product:
            print(f"Warning: Record at index {idx} (Sale {sale_id}) "
                  f"has no Product, skipping.")
            continue

        quantity = record.get("Quantity")
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            print(f"Warning: Record at index {idx} (Sale {sale_id}) "
                  f"has invalid Quantity '{quantity}', skipping.")
            continue

        if product not in catalogue:
            print(f"Warning: Product '{product}' not found in catalogue, "
                  f"skipping record at index {idx}.")
            continue

        unit_price = catalogue[product]
        line_total = unit_price * quantity

        if sale_id not in sale_totals:
            sale_totals[sale_id] = {
                "date": record.get("SALE_Date", "N/A"),
                "items": [],
                "total": 0.0,
            }

        sale_totals[sale_id]["items"].append({
            "product": product,
            "quantity": quantity,
            "unit_price": unit_price,
            "line_total": line_total,
        })
        sale_totals[sale_id]["total"] += line_total
        grand_total += line_total

    return sale_totals, grand_total


def format_results(sale_totals, grand_total, elapsed, detailed=True):
    """Format the results into a human-readable string.

    Args:
        sale_totals: Dict of sale summaries from compute_sales.
        grand_total: Overall total across all sales.
        elapsed: Elapsed time in seconds.
        detailed: If True, show full per-sale breakdown.
                  If False, show only the grand total.

    Returns:
        Formatted results string.
    """
    separator = "=" * 60
    lines = [
        "**** SALES REPORT ****",
        "",
    ]

    if detailed:
        for sale_id in sorted(sale_totals):
            sale = sale_totals[sale_id]
            lines.append(f"Sale ID: {sale_id}  |  Date: {sale['date']}")
            lines.append("-" * 60)
            lines.append(f"  {'Product':<35} {'Qty':>4} {'Unit $':>9} "
                         f"{'Total $':>10}")
            lines.append(f"  {'-'*35} {'-'*4} {'-'*9} {'-'*10}")

            for item in sale["items"]:
                lines.append(
                    f"  {item['product']:<35} {item['quantity']:>4} "
                    f"{item['unit_price']:>9.2f} "
                    f"{item['line_total']:>10.2f}"
                )

            lines.append(f"  {'':>50} {'----------':>10}")
            lines.append(
                f"  {'Sale Total':>50} {sale['total']:>10.2f}"
            )
            lines.append("")

    lines.append(separator)
    lines.append(f"  GRAND TOTAL: ${grand_total:,.2f}")
    lines.append(separator)
    lines.append(f"  Time elapsed: {elapsed:.4f} seconds")
    lines.append(separator)

    return "\n".join(lines)


def write_results(text, filepath="SalesResults.txt"):
    """Write results text to a file.

    Args:
        text: The formatted results string.
        filepath: Output file path.
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(text + "\n")
    except PermissionError:
        print(f"Error: Permission denied writing to '{filepath}'.")
    except OSError as exc:
        print(f"Error: Could not write to '{filepath}': {exc}")


def parse_args(argv=None):
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        argparse.Namespace with catalogue, sales, and detail attributes.
    """
    parser = argparse.ArgumentParser(
        description="Compute total sales from a product catalogue "
                    "and sales record."
    )
    parser.add_argument(
        "catalogue",
        help="Path to the JSON product catalogue file."
    )
    parser.add_argument(
        "sales",
        help="Path to the JSON sales record file."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--total",
        action="store_true",
        default=True,
        help="Show only the grand total."
    )
    group.add_argument(
        "--detail",
        action="store_true",

        help="Show the full detailed report (default)."
    )
    args = parser.parse_args(argv)
    if args.total:
        args.detail = False
    return args


def main(argv=None):
    """Entry point: parse args, load data, compute, and output.

    Args:
        argv: Optional argument list for testing (defaults to sys.argv).
    """
    args = parse_args(argv)

    start_time = time.time()

    products = load_json(args.catalogue)
    if not isinstance(products, list):
        print("Error: Product catalogue must be a JSON array.")
        sys.exit(1)

    sales_records = load_json(args.sales)
    if not isinstance(sales_records, list):
        print("Error: Sales record must be a JSON array.")
        sys.exit(1)

    catalogue = build_price_catalogue(products)
    if not catalogue:
        print("Error: No valid products found in catalogue.")
        sys.exit(1)

    sale_totals, grand_total = compute_sales(catalogue, sales_records)

    elapsed = time.time() - start_time

    results = format_results(
        sale_totals, grand_total, elapsed, detailed=args.detail
    )
    print(results)
    write_results(results)
    print("\nResults saved to SalesResults.txt")


if __name__ == "__main__":
    main()
