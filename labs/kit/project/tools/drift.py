"""Drift per feature and per week against the training data (lab 4.3).

    uv run python tools/drift.py --reference ../data/claims.csv --weeks ../data/replay/week1.csv ../data/replay/week2.csv \
        ../data/replay/week3.csv ../data/replay/week4.csv --out runs/drift.json

Two statistics per feature: the population stability index (PSI) over the training data's deciles
(or its categories), which measures how much the distribution moved; and, for numeric features, the
two-sample Kolmogorov-Smirnov test, whose p-value says only whether a move can be told from chance.
Rifd's monitoring policy: PSI below 0.1 is stable, 0.1 to 0.25 is worth watching, 0.25 or more is shifted.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import ks_2samp

NUMERIC = ["amount_sar", "policy_tenure_months", "prior_claims_12m", "days_to_report", "vehicle_age_years"]
CATEGORICAL = ["line", "region", "channel"]
TRAINING_ROWS = 40000
WATCH, SHIFTED = 0.10, 0.25
EPS = 1e-4
MARK = {"shifted": "SHIFTED", "watch": "watch", "stable": ""}


def read(path: str, limit: int | None = None) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[:limit] if limit else rows


def numbers(rows: list[dict], feature: str) -> np.ndarray:
    return np.array([float(r[feature]) for r in rows if r[feature] != ""])


def psi_from_shares(expected: np.ndarray, actual: np.ndarray) -> float:
    e = np.clip(expected, EPS, None)
    a = np.clip(actual, EPS, None)
    return float(np.sum((a - e) * np.log(a / e)))


def psi_numeric(ref: np.ndarray, cur: np.ndarray, bins: int = 10) -> float:
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -math.inf, math.inf
    e = np.histogram(ref, edges)[0] / len(ref)
    a = np.histogram(cur, edges)[0] / len(cur)
    return psi_from_shares(e, a)


def psi_categorical(ref: list[str], cur: list[str]) -> float:
    cats = sorted(set(ref) | set(cur))
    e = np.array([ref.count(c) for c in cats]) / len(ref)
    a = np.array([cur.count(c) for c in cats]) / len(cur)
    return psi_from_shares(e, a)


def verdict(psi: float) -> str:
    return "shifted" if psi >= SHIFTED else ("watch" if psi >= WATCH else "stable")


def week_report(reference: list[dict], rows: list[dict]) -> dict:
    out = {}
    for f in NUMERIC:
        ref, cur = numbers(reference, f), numbers(rows, f)
        if len(ref) == 0 or len(cur) == 0:
            continue  # a field this segment does not have, such as vehicle age for health claims
        ks = ks_2samp(ref, cur)
        psi = psi_numeric(ref, cur)
        out[f] = {"psi": round(psi, 4), "ks": round(float(ks.statistic), 4), "p_value": float(f"{ks.pvalue:.3g}"), "verdict": verdict(psi)}
    for f in CATEGORICAL:
        psi = psi_categorical([r[f] for r in reference], [r[f] for r in rows])
        out[f] = {"psi": round(psi, 4), "verdict": verdict(psi)}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reference", default="../data/claims.csv")
    ap.add_argument("--weeks", nargs="+", required=True)
    ap.add_argument("--by", help="also compute every statistic within each value of this column, such as line")
    ap.add_argument("--out", default="runs/drift.json")
    a = ap.parse_args()
    reference = read(a.reference, TRAINING_ROWS)
    report = {}
    for path in a.weeks:
        rows = read(path)
        report[Path(path).stem] = week_report(reference, rows)
        if a.by:
            for value in sorted({r[a.by] for r in reference}):
                ref_part = [r for r in reference if r[a.by] == value]
                cur_part = [r for r in rows if r[a.by] == value]
                part = week_report(ref_part, cur_part)
                for f, c in part.items():
                    if f != a.by:
                        report[Path(path).stem][f"{f}|{a.by}={value}"] = c
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    feats = list(next(iter(report.values())).keys())
    print("PSI by week (KS p-value in brackets for numeric features)")
    print(f"{'feature':<34}" + "".join(f"{w:>24}" for w in report))
    for f in feats:
        cells = []
        for w in report.values():
            c = w.get(f, {"psi": float("nan"), "verdict": "stable"})
            p = f" ({c['p_value']:.0e})" if "p_value" in c else ""
            cells.append(f"{c['psi']:.3f}{p} {MARK[c['verdict']]}".rstrip())
        print(f"{f:<34}" + "".join(f"{x:>24}" for x in cells))
    last = list(report.values())[-1]
    shifted = [f for f in feats if last[f]["verdict"] == "shifted"]
    print(f"shifted in the last week: {', '.join(shifted) or 'none'}")


if __name__ == "__main__":
    main()
