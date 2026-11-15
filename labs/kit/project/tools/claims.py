"""Turn rows of the claims files into requests of the contract (shared by the replay and load tools)."""

from __future__ import annotations

import csv
from pathlib import Path


def read(path: str | Path, limit: int | None = None) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[:limit] if limit else rows


def request_body(row: dict) -> dict:
    """The JSON a caller (Rifd's claims system) sends: the claim, its description and the member."""
    body = {
        "claim_id": row["claim_id"], "line": row["line"], "region": row["region"], "channel": row["channel"],
        "amount_sar": float(row["amount_sar"]), "policy_tenure_months": int(row["policy_tenure_months"]),
        "prior_claims_12m": int(row["prior_claims_12m"]), "days_to_report": int(row["days_to_report"]),
        "description": row["description"],
        "member": {"name": row["member_name"], "national_id": row["national_id"], "mobile": row["mobile"]},
    }
    if row["vehicle_age_years"] != "":
        body["vehicle_age_years"] = int(row["vehicle_age_years"])
    if row["police_report"] != "":
        body["police_report"] = row["police_report"] == "1"
    if row["in_network"] != "":
        body["in_network"] = row["in_network"] == "1"
    return body
