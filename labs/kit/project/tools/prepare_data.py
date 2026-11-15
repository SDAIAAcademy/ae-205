"""Write the synthetic claims of Rifd Mutual Insurance into a data folder.

    uv run python tools/prepare_data.py --out ../data

Fixed seed: the same files on every run. Every person, number and claim is invented.
Files:
  claims.csv            50,000 historic claims with their triage label (training and history)
  replay/week1..4.csv   3,000 new claims a week; drift is injected from week 3
  replay/labels_week1.csv, labels_week2.csv   the delayed labels that have arrived so far
  objective.json        Munira's latency objective and target rate
  price_sheet.json      Rifd's in-Kingdom hosting quote (invented prices)
  rollback_criteria.json, rollback_criteria.md   written before any release
  recordings/spike.jsonl   a recorded scrape series with an error spike (lab 4.4)
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

SEED = 205
LINES = ["motor", "health", "property"]
REGIONS = ["riyadh", "makkah", "eastern", "madinah", "qassim", "asir"]
CHANNELS = ["app", "branch", "broker"]
LABELS = ["fast_track", "standard", "investigate"]

INCIDENTS = {
    "motor": [
        ("rear_collision", "Rear bumper and boot lid damaged when another car hit us at a junction", "تضرر الصدام الخلفي وغطاء الصندوق بعد اصطدام سيارة أخرى بنا عند التقاطع"),
        ("windscreen", "Windscreen cracked by a stone on the highway", "تشقق الزجاج الأمامي بسبب حجر على الطريق السريع"),
        ("parking", "Side door scratched and dented in a parking lot", "خدش وانبعاج في الباب الجانبي في موقف السيارات"),
        ("flood", "Car engine stopped after driving through flood water", "توقف محرك السيارة بعد السير في مياه السيول"),
        ("theft", "Car stolen from outside the house at night", "سرقة السيارة من أمام المنزل ليلا"),
    ],
    "health": [
        ("outpatient", "Outpatient visit and blood tests for a fever", "زيارة عيادة خارجية وتحاليل دم بسبب الحمى"),
        ("emergency", "Emergency room visit after a fall, x-ray of the wrist", "زيارة الطوارئ بعد سقوط وأشعة على المعصم"),
        ("dental", "Dental filling and cleaning", "حشوة أسنان وتنظيف"),
        ("maternity", "Delivery and two nights in hospital", "ولادة وليلتان في المستشفى"),
        ("pharmacy", "Prescription medicines for a chronic condition", "أدوية بوصفة طبية لمرض مزمن"),
    ],
    "property": [
        ("water_leak", "Water leak from a pipe damaged the kitchen ceiling", "تسرب مياه من أنبوب أتلف سقف المطبخ"),
        ("fire", "Small kitchen fire damaged cabinets and walls", "حريق صغير في المطبخ أتلف الخزائن والجدران"),
        ("burglary", "Home burglary, electronics and jewellery taken", "سطو على المنزل وسرقة أجهزة ومجوهرات"),
        ("storm", "Storm damaged the roof and the outdoor unit of the air conditioner", "عاصفة أتلفت السطح والوحدة الخارجية للمكيف"),
        ("glass", "Broken window glass in the living room", "كسر زجاج نافذة غرفة المعيشة"),
    ],
}
DETAILS_EN = ["Photos attached.", "Reported the same day.", "Second claim this year.", "Invoice attached.", "Waiting for the workshop estimate.", "Police report number attached.", ""]
DETAILS_AR = ["الصور مرفقة.", "تم الإبلاغ في اليوم نفسه.", "المطالبة الثانية هذا العام.", "الفاتورة مرفقة.", "بانتظار تقدير الورشة.", "رقم محضر الشرطة مرفق.", ""]
FIRST = ["Abdullah", "Mohammed", "Fatimah", "Aisha", "Khalid", "Sarah", "Hassan", "Maryam", "Omar", "Noor", "Yasser", "Hessa", "Ali", "Ruqayya", "Saleh", "Arwa"]
LAST = ["Al-Harbi", "Al-Qahtani", "Al-Ghamdi", "Al-Dosari", "Al-Shehri", "Al-Zahrani", "Al-Mutairi", "Al-Otaibi", "Al-Anazi", "Al-Shammari", "Al-Malki", "Al-Juhani"]

FIELDS = ["claim_id", "day", "line", "incident", "region", "channel", "amount_sar", "policy_tenure_months",
          "prior_claims_12m", "days_to_report", "vehicle_age_years", "police_report", "in_network",
          "description", "member_name", "national_id", "mobile", "label"]


def draw(rng: np.random.Generator, n: int, start_id: int, day0: int, days: int, *, drift: bool = False, tenure_shift: float = 0.0) -> list[dict]:
    line_p = [0.5, 0.35, 0.15]
    chan_p = [0.70, 0.18, 0.12] if drift else [0.45, 0.30, 0.25]
    rows = []
    for i in range(n):
        line = LINES[rng.choice(3, p=line_p)]
        inc_i = int(rng.integers(0, 5))
        incident, en, ar = INCIDENTS[line][inc_i]
        region = REGIONS[rng.choice(6, p=[0.32, 0.24, 0.18, 0.1, 0.08, 0.08])]
        channel = CHANNELS[rng.choice(3, p=chan_p)]
        base = {"motor": 7.9, "health": 6.9, "property": 8.6}[line] + 0.35 * inc_i / 4
        amount = float(np.exp(rng.normal(base, 0.75)))
        if drift and line == "motor":
            amount *= 1.6  # parts prices rose: the planted shift of weeks 3 and 4, motor only
        amount = round(min(amount, 900000.0), 2)
        tenure = int(max(0, min(480, rng.gamma(2.0, 18.0) + tenure_shift)))
        prior = int(min(12, rng.poisson(0.6)))
        days_to_report = int(min(365, rng.exponential(4.0)))
        vehicle_age = int(min(30, rng.gamma(2.2, 2.5))) if line == "motor" else None
        police = bool(rng.random() < 0.7) if line == "motor" else None
        in_net = bool(rng.random() < 0.8) if line == "health" else None
        # the triage label: a hidden risk score with noise
        risk = (0.9 * (math.log(amount) - base) + 0.45 * prior + 0.04 * min(days_to_report, 60)
                - 0.012 * min(tenure, 120) + (0.9 if police is False else 0.0) + (0.7 if in_net is False else 0.0)
                + (1.2 if incident in ("theft", "burglary", "fire") else 0.0) + (0.3 if channel == "broker" else 0.0)
                + (1.1 if tenure < 4 else 0.0) + (0.9 if days_to_report > 20 else 0.0)
                + (0.8 if (vehicle_age or 0) > 12 and amount > 6000 else 0.0)
                + rng.normal(0, 0.35))
        label = "investigate" if risk > 1.55 else ("standard" if risk > 0.05 else "fast_track")
        arabic = rng.random() < 0.45
        detail = (DETAILS_AR if arabic else DETAILS_EN)[int(rng.integers(0, 7))]
        text = ((ar if arabic else en) + " " + detail).strip()
        rows.append({
            "claim_id": f"CLM-{start_id + i:06d}",
            "day": day0 + int(rng.integers(0, days)),
            "line": line, "incident": incident, "region": region, "channel": channel,
            "amount_sar": amount, "policy_tenure_months": tenure, "prior_claims_12m": prior,
            "days_to_report": days_to_report,
            "vehicle_age_years": "" if vehicle_age is None else vehicle_age,
            "police_report": "" if police is None else int(police),
            "in_network": "" if in_net is None else int(in_net),
            "description": text,
            "member_name": f"{FIRST[int(rng.integers(0, 16))]} {LAST[int(rng.integers(0, 12))]}",
            "national_id": "1" + "".join(str(int(d)) for d in rng.integers(0, 10, 9)),
            "mobile": "05" + "".join(str(int(d)) for d in rng.integers(0, 10, 8)),
            "label": label,
        })
    return rows


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def spike_series() -> list[dict]:
    """A 30-minute scrape recording every 15 s: an error spike from minute 12 to 18, a one-minute
    latency blip at minute 6 and a sustained latency rise from minute 22."""
    rng = np.random.default_rng(SEED + 4)
    buckets = [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0, 2.5]
    total = {"200": 0.0, "422": 0.0, "500": 0.0}
    hist = [0.0] * len(buckets)
    count = 0.0
    total_sum = 0.0
    out = []
    for step in range(121):
        t = step * 15
        minute = t / 60
        reqs = rng.poisson(40 * 15)
        err_rate = 0.08 if 12 <= minute < 18 else 0.002
        errs = rng.binomial(reqs, err_rate)
        bad = rng.binomial(reqs, 0.01)
        total["500"] += errs
        total["422"] += bad
        total["200"] += reqs - errs - bad
        slow = (6 <= minute < 7) or minute >= 22
        mu = math.log(0.11 if slow else 0.035)
        lat = np.exp(rng.normal(mu, 0.45, reqs))
        for j, b in enumerate(buckets):
            hist[j] += float((lat <= b).sum())
        count += reqs
        total_sum += float(lat.sum())
        samples = {}
        for code, v in total.items():
            samples[f'rifd_requests_total{{route="/v1/triage",status="{code}"}}'] = v
        for j, b in enumerate(buckets):
            samples[f'rifd_request_duration_seconds_bucket{{route="/v1/triage",le="{b}"}}'] = hist[j]
        samples['rifd_request_duration_seconds_bucket{route="/v1/triage",le="+Inf"}'] = count
        samples['rifd_request_duration_seconds_count{route="/v1/triage"}'] = count
        samples['rifd_request_duration_seconds_sum{route="/v1/triage"}'] = round(total_sum, 4)
        out.append({"t": t, "samples": samples})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    out = Path(ap.parse_args().out)
    rng = np.random.default_rng(SEED)
    history = draw(rng, 50000, 1, 0, 364)
    history.sort(key=lambda r: (r["day"], r["claim_id"]))
    write_csv(out / "claims.csv", history, FIELDS)
    weeks = {}
    next_id = 50001
    for w in range(1, 5):
        drift = w >= 3
        rows = draw(np.random.default_rng(SEED + w), 3000, next_id, 364 + 7 * (w - 1), 7, drift=drift, tenure_shift=1.0 if w >= 2 else 0.0)
        next_id += 3000
        rows.sort(key=lambda r: (r["day"], r["claim_id"]))
        weeks[w] = rows
        write_csv(out / "replay" / f"week{w}.csv", rows, [f for f in FIELDS if f != "label"])
    for w in (1, 2):
        write_csv(out / "replay" / f"labels_week{w}.csv", weeks[w], ["claim_id", "label"])
    (out / "objective.json").write_text(json.dumps({
        "owner": "Munira Al-Ajmi, head of claims operations",
        "service": "farz /v1/triage",
        "p95_ms": 150, "target_rps": 200, "error_ratio_max": 0.01,
        "note": "Peak after a sandstorm or a flood: 200 claims a second for triage. p95 at or under 150 ms, measured by the caller."
    }, indent=2) + "\n", encoding="utf-8")
    (out / "price_sheet.json").write_text(json.dumps({
        "provider": "Rifd's in-Kingdom hosting quote (invented prices for the course)",
        "currency": "SAR",
        "vcpu_hour": 0.19, "gib_hour": 0.025, "gpu_hour": 7.40,
        "billing": "per container, on its requests, per hour"
    }, indent=2) + "\n", encoding="utf-8")
    criteria = {
        "owner": "Munira Al-Ajmi decides; the on-call engineer executes",
        "min_canary_requests": 200,
        "error_ratio_max": 0.01,
        "p95_ms_max": 150,
        "label_share_max_diff": 0.10,
        "rollback_within_seconds": 300
    }
    (out / "rollback_criteria.json").write_text(json.dumps(criteria, indent=2) + "\n", encoding="utf-8")
    (out / "rollback_criteria.md").write_text(
        "# Rollback criteria for a Farz release\n\n"
        "Written by Munira Al-Ajmi (head of claims operations) before the release. She decides; the on-call engineer executes.\n\n"
        "Judge the canary only after it has served at least 200 requests. Roll back when any one holds:\n\n"
        "1. The canary's error ratio (status 500 or 503) is above 1%.\n"
        "2. The canary's 95th-percentile latency is above 150 ms.\n"
        "3. The share of any triage label in the canary differs from the current version's by more than 10 points.\n\n"
        "Roll back first, diagnose second: the canary's traffic share goes to 0 within 5 minutes of a criterion firing.\n",
        encoding="utf-8")
    rec = out / "recordings" / "spike.jsonl"
    rec.parent.mkdir(parents=True, exist_ok=True)
    rec.write_text("".join(json.dumps(s) + "\n" for s in spike_series()), encoding="utf-8")
    shares = {lab: round(sum(r["label"] == lab for r in history) / len(history), 4) for lab in LABELS}
    print(f"wrote {len(history)} claims, 4 replay weeks of 3000, label shares {shares}")


if __name__ == "__main__":
    main()
