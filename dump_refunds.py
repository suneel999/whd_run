"""Print paid runners (pending → success with screenshot) for ₹250 refunds."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import db

OUT = Path(__file__).resolve().parent / "data" / "pulse-run-refunds.csv"


def main() -> int:
    rows = db.list_paid()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Name", "Mobile number", "Email", "T-shirt size", "Registered at", "Amount (INR)"])
        for row in rows:
            writer.writerow(
                [row["name"], row["phone"], row.get("email") or "", row["tshirt"], row["created_at"], 250]
            )
        writer.writerow(["Total people", len(rows), "", "", "", len(rows) * 250])
    print(f"{len(rows)} people to refund Rs 250 each. Total Rs {len(rows) * 250}")
    print("Name\tMobile\tEmail\tSize\tRegistered")
    for row in rows:
        print(f"{row['name']}\t{row['phone']}\t{row.get('email') or ''}\t{row['tshirt']}\t{row['created_at']}")
    print(f"Saved {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
