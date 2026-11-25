"""Deterministic checks for either experiment's machine-readable deliverables."""
import argparse
import csv
import json
import re
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "inputs/price_catalog.csv"
ACTIVITIES = (
    "welcome_checkin", "icebreaker", "career_panel", "structured_networking",
    "refreshment_break", "closing_activity",
)
COVERAGE = ("food", "drink", "name_tags")


def read_json(path):
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"{path}: JSON file is missing") from exc
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path}: JSON file must be UTF-8") from exc
    if not content.strip():
        raise ValueError(f"{path}: JSON file is empty")
    try:
        value = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON at line {exc.lineno}, column {exc.colno} "
                         f"({exc.msg})") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def minutes(value):
    if isinstance(value, str) and re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", value):
        hours, mins = map(int, value.split(":"))
        return hours * 60 + mins
    raise ValueError(f"Invalid agenda time: {value!r}")


def check_schedule(plan):
    errors = []
    agenda = plan["agenda"]
    if not isinstance(agenda, list) or tuple(row["activity"] for row in agenda) != ACTIVITIES:
        return ["Agenda must list all six activities once in the required order."]
    previous_end = 16 * 60
    for row in agenda:
        activity = row["activity"]
        start, end = minutes(row["start"]), minutes(row["end"])
        if start != previous_end or not 16 * 60 <= start < end <= 19 * 60:
            errors.append(f"{activity}: invalid block or gap/overlap.")
        previous_end = end
        volunteers = row["volunteers"]
        if (not isinstance(volunteers, list) or not 1 <= len(volunteers) <= 6
                or any(v not in ("V1", "V2", "V3", "V4", "V5", "V6") for v in volunteers)
                or len(volunteers) != len(set(volunteers))):
            errors.append(f"{activity}: assign distinct volunteers from V1 through V6.")
    if previous_end != 19 * 60:
        errors.append("Agenda must end at 19:00.")
    return errors


def check_budget(budget, catalog_file):
    with catalog_file.open(newline="", encoding="utf-8") as stream:
        catalog = {row["sku"]: row for row in csv.DictReader(stream)}
    errors = []
    coverage = dict.fromkeys(COVERAGE, 0)
    subtotal = 0
    seen = set()
    items = budget["items"]
    if not isinstance(items, list):
        return ["Budget items must be an array."]
    for row in items:
        sku, quantity = row["sku"], row["quantity"]
        if sku not in catalog or sku in seen:
            errors.append(f"Unknown or duplicated SKU: {sku!r}.")
            continue
        seen.add(sku)
        if type(quantity) is not int or quantity < 1:
            errors.append(f"{sku}: quantity must be a positive whole number.")
            continue
        price = int(catalog[sku]["unit_cents"])
        line = quantity * price
        for field, expected in (("unit_cents", price), ("total_cents", line)):
            if type(row[field]) is not int or row[field] != expected:
                errors.append(f"{sku}: {field} must be {expected}.")
        subtotal += line
        category = catalog[sku]["category"]
        if category in coverage:
            coverage[category] += quantity * int(catalog[sku]["units_per_pack"])
    for category, count in coverage.items():
        if count < 50:
            errors.append(f"{category}: covers {count} of 50 attendees.")
    if type(budget["subtotal_cents"]) is not int or budget["subtotal_cents"] != subtotal:
        errors.append(f"Subtotal must be {subtotal} cents.")
    reserve = budget["reserve_cents"]
    if type(reserve) is not int or reserve < 3000:
        errors.append("Reserve must be an integer of at least 3000 cents.")
    if type(reserve) is int:
        total = subtotal + reserve
        if total > 30000:
            errors.append("Budget including reserve exceeds 30000 cents.")
        if type(budget["total_cents"]) is not int or budget["total_cents"] != total:
            errors.append(f"Total must be {total} cents.")
    return errors


def validate(logistics, budget, catalog=CATALOG):
    errors = []
    for label, check in (
        ("logistics", lambda: check_schedule(read_json(logistics))),
        ("budget", lambda: check_budget(read_json(budget), catalog)),
    ):
        try:
            errors.extend(check())
        except (OSError, ValueError, TypeError, KeyError) as exc:
            errors.append(f"{label}: {exc}")
    return {"passed": not errors, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logistics", type=Path)
    parser.add_argument("budget", type=Path)
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    args = parser.parse_args()
    report = validate(args.logistics, args.budget, args.catalog)
    print(json.dumps(report, indent=2))
    return int(not report["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
