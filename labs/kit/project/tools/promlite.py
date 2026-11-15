"""A small stand-in for Prometheus, for laptops without it: scrape, record, query, test alert rules.

    uv run python tools/promlite.py record --url http://127.0.0.1:8000/metrics --every 2 --for 60 --out series.jsonl
    uv run python tools/promlite.py query --series series.jsonl --expr 'histogram_quantile(0.95, sum by (le) (rate(rifd_request_duration_seconds_bucket[30s])))'
    uv run python tools/promlite.py rules --series ../data/recordings/spike.jsonl --rules monitoring/alerts.yml

It understands the part of PromQL the course uses: a selector with label matchers, rate(x[w]),
sum and sum by (labels), histogram_quantile, the four arithmetic operators, a comparison with a
number, and numbers. Real Prometheus reads the same expressions and the same rule files.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
import urllib.request
from pathlib import Path

import yaml

Labels = tuple  # sorted tuple of (name, value) pairs
SAMPLE = re.compile(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)(\{[^}]*\})?\s+(\S+)$')
LABEL = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*(=~|!=|=)\s*"((?:[^"\\]|\\.)*)"')
DURATION = re.compile(r'^(\d+)(ms|s|m|h)$')


def seconds(d: str) -> float:
    m = DURATION.match(d)
    if not m:
        raise ValueError(f"not a duration: {d}")
    return int(m.group(1)) * {"ms": 0.001, "s": 1, "m": 60, "h": 3600}[m.group(2)]


def parse_exposition(text: str) -> dict[str, float]:
    out = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        m = SAMPLE.match(line.strip())
        if m:
            out[(m.group(1) + (m.group(2) or "")).replace("_total{", "_total{")] = float(m.group(3))
    return out


def split_key(key: str) -> tuple[str, Labels]:
    if "{" not in key:
        return key, ()
    name, rest = key.split("{", 1)
    return name, tuple(sorted((k, v) for k, _, v in LABEL.findall(rest)))


# ---------- the series ----------

class Series:
    def __init__(self, rows: list[dict]):
        self.times = [r["t"] for r in rows]
        self.data: dict[tuple[str, Labels], list[float | None]] = {}
        for i, r in enumerate(rows):
            for key, v in r["samples"].items():
                k = split_key(key)
                self.data.setdefault(k, [None] * len(rows))[i] = v

    @classmethod
    def load(cls, path: str) -> "Series":
        return cls([json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()])


# ---------- the expression language ----------

TOKEN = re.compile(r'\s*(?:(\d+(?:\.\d+)?(?:e-?\d+)?)|([a-zA-Z_:][a-zA-Z0-9_:]*)|(\{[^}]*\})|(\[[^\]]+\])|(>=|<=|==|!=|[()+\-*/<>,]))')


def tokens(expr: str) -> list[str]:
    out, pos = [], 0
    expr = expr.strip()
    while pos < len(expr):
        m = TOKEN.match(expr, pos)
        if not m or m.end() == pos:
            raise ValueError(f"cannot read the expression at: {expr[pos:pos + 20]!r}")
        out.append(next(g for g in m.groups() if g is not None))
        pos = m.end()
    return out


class Parser:
    def __init__(self, expr: str):
        self.t = tokens(expr)
        self.i = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def take(self, want=None):
        tok = self.peek()
        if want is not None and tok != want:
            raise ValueError(f"expected {want!r}, found {tok!r}")
        self.i += 1
        return tok

    def parse(self):
        node = self.comparison()
        if self.peek() is not None:
            raise ValueError(f"unexpected {self.peek()!r}")
        return node

    def comparison(self):
        left = self.additive()
        if self.peek() in (">", "<", ">=", "<=", "==", "!="):
            op = self.take()
            return ("cmp", op, left, self.additive())
        return left

    def additive(self):
        node = self.term()
        while self.peek() in ("+", "-"):
            node = ("bin", self.take(), node, self.term())
        return node

    def term(self):
        node = self.atom()
        while self.peek() in ("*", "/"):
            node = ("bin", self.take(), node, self.atom())
        return node

    def atom(self):
        tok = self.take()
        if tok == "(":
            node = self.comparison()
            self.take(")")
            return node
        if re.match(r'^\d', tok):
            return ("num", float(tok))
        if tok == "rate":
            self.take("(")
            name = self.take()
            matchers = self.matchers()
            window = self.take()
            if not window.startswith("["):
                raise ValueError("rate() needs a range, such as [5m]")
            self.take(")")
            return ("rate", name, matchers, seconds(window[1:-1]))
        if tok == "sum":
            by = None
            if self.peek() == "by":
                self.take()
                self.take("(")
                by = []
                while self.peek() != ")":
                    t = self.take()
                    if t != ",":
                        by.append(t)
                self.take(")")
            self.take("(")
            inner = self.comparison()
            self.take(")")
            return ("sum", tuple(by) if by is not None else None, inner)
        if tok == "histogram_quantile":
            self.take("(")
            q = float(self.take())
            self.take(",")
            inner = self.comparison()
            self.take(")")
            return ("hq", q, inner)
        if re.match(r'^[a-zA-Z_:]', tok):
            return ("sel", tok, self.matchers())
        raise ValueError(f"unexpected {tok!r}")

    def matchers(self):
        if self.peek() and self.peek().startswith("{"):
            return [(k, op, v) for k, op, v in LABEL.findall(self.take())]
        return []


def match(labels: Labels, matchers) -> bool:
    d = dict(labels)
    for k, op, v in matchers:
        have = d.get(k, "")
        if op == "=" and have != v:
            return False
        if op == "!=" and have == v:
            return False
        if op == "=~" and not re.fullmatch(v, have):
            return False
    return True


def evaluate(node, s: Series, i: int):
    """Evaluate at step i. A vector is a dict {labels: value}; a scalar is a float."""
    kind = node[0]
    if kind == "num":
        return node[1]
    if kind == "sel":
        _, name, m = node
        return {lab: vals[i] for (n, lab), vals in s.data.items() if n == name and match(lab, m) and vals[i] is not None}
    if kind == "rate":
        _, name, m, window = node
        t_now = s.times[i]
        j = i
        while j > 0 and s.times[j - 1] >= t_now - window:
            j -= 1
        if j == i:
            return {}
        out = {}
        for (n, lab), vals in s.data.items():
            if n != name or not match(lab, m) or vals[i] is None or vals[j] is None:
                continue
            delta = vals[i] - vals[j]
            if delta < 0:  # a counter reset: the process restarted
                delta = vals[i]
            out[tuple(x for x in lab)] = delta / (s.times[i] - s.times[j])
        return out
    if kind == "sum":
        _, by, inner = node
        v = evaluate(inner, s, i)
        if not isinstance(v, dict):
            return v
        if by is None:
            return {(): sum(v.values())} if v else {}
        out: dict = {}
        for lab, val in v.items():
            key = tuple(sorted((k, x) for k, x in lab if k in by))
            out[key] = out.get(key, 0.0) + val
        return out
    if kind == "hq":
        _, q, inner = node
        v = evaluate(inner, s, i)
        groups: dict = {}
        for lab, val in v.items():
            d = dict(lab)
            le = d.pop("le", None)
            if le is None:
                continue
            groups.setdefault(tuple(sorted(d.items())), []).append((math.inf if le == "+Inf" else float(le), val))
        return {g: quantile(q, sorted(b)) for g, b in groups.items()}
    if kind == "bin":
        _, op, a, b = node
        return combine(op, evaluate(a, s, i), evaluate(b, s, i))
    if kind == "cmp":
        _, op, a, b = node
        left, right = evaluate(a, s, i), evaluate(b, s, i)
        test = {">": lambda x, y: x > y, "<": lambda x, y: x < y, ">=": lambda x, y: x >= y,
                "<=": lambda x, y: x <= y, "==": lambda x, y: x == y, "!=": lambda x, y: x != y}[op]
        if isinstance(left, dict):
            return {k: v for k, v in left.items() if not math.isnan(v) and test(v, right if not isinstance(right, dict) else right.get(k, math.nan))}
        return left if test(left, right) else {}
    raise ValueError(kind)


def combine(op, a, b):
    f = {"+": lambda x, y: x + y, "-": lambda x, y: x - y, "*": lambda x, y: x * y,
         "/": lambda x, y: x / y if y else math.nan}[op]
    if isinstance(a, dict) and isinstance(b, dict):
        if list(b.keys()) == [()]:
            return {k: f(v, b[()]) for k, v in a.items()}
        return {k: f(v, b[k]) for k, v in a.items() if k in b}
    if isinstance(a, dict):
        return {k: f(v, b) for k, v in a.items()}
    if isinstance(b, dict):
        return {k: f(a, v) for k, v in b.items()}
    return f(a, b)


def quantile(q: float, buckets: list[tuple[float, float]]) -> float:
    """Prometheus' estimate: find the bucket holding the q-th observation, interpolate linearly inside it."""
    if not buckets or buckets[-1][1] == 0:
        return math.nan
    total = buckets[-1][1]
    rank = q * total
    prev_le, prev_count = 0.0, 0.0
    for le, count in buckets:
        if count >= rank:
            if math.isinf(le):
                return prev_le
            if count == prev_count:
                return le
            return prev_le + (le - prev_le) * (rank - prev_count) / (count - prev_count)
        prev_le, prev_count = le, count
    return prev_le


def query(series: Series, expr: str) -> list[tuple[float, object]]:
    node = Parser(expr).parse()
    return [(series.times[i], evaluate(node, series, i)) for i in range(len(series.times))]


def run_rules(series: Series, rules_file: str) -> list[dict]:
    doc = yaml.safe_load(Path(rules_file).read_text(encoding="utf-8"))
    rules = [r for g in doc.get("groups", []) for r in g.get("rules", []) if "alert" in r]
    if not rules:
        raise ValueError(f"no alert rules in {rules_file}")
    report = []
    for rule in rules:
        node = Parser(rule["expr"]).parse()
        hold = seconds(rule["for"]) if rule.get("for") else 0
        pending_since = None
        firing = []
        state = "inactive"
        for i, t in enumerate(series.times):
            v = evaluate(node, series, i)
            active = bool(v) if isinstance(v, dict) else bool(v)
            if active:
                pending_since = t if pending_since is None else pending_since
                if t - pending_since >= hold and state != "firing":
                    state = "firing"
                    firing.append({"from_s": t, "to_s": None})
            else:
                if state == "firing":
                    firing[-1]["to_s"] = t
                state, pending_since = "inactive", None
        report.append({"alert": rule["alert"], "for": rule.get("for", "0s"), "severity": rule.get("labels", {}).get("severity", ""),
                       "fired": firing, "has_runbook": "runbook_url" in rule.get("annotations", {})})
    return report


def record(url: str, every: float, duration: float, out: str) -> None:
    start = time.monotonic()
    with open(out, "w", encoding="utf-8") as f:
        while (now := time.monotonic() - start) <= duration:
            text = urllib.request.urlopen(url, timeout=5).read().decode()
            f.write(json.dumps({"t": round(now, 2), "samples": parse_exposition(text)}) + "\n")
            f.flush()
            time.sleep(every)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="promlite")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--url", required=True)
    r.add_argument("--every", type=float, default=2)
    r.add_argument("--for", dest="duration", type=float, default=60)
    r.add_argument("--out", required=True)
    q = sub.add_parser("query")
    q.add_argument("--series", required=True)
    q.add_argument("--expr", required=True)
    q.add_argument("--last", action="store_true", help="print only the last step")
    ru = sub.add_parser("rules")
    ru.add_argument("--series", required=True)
    ru.add_argument("--rules", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "record":
        record(a.url, a.every, a.duration, a.out)
        return 0
    s = Series.load(a.series)
    if a.cmd == "query":
        rows = query(s, a.expr)
        for t, v in (rows[-1:] if a.last else rows):
            shown = {",".join(f"{k}={x}" for k, x in lab) or "{}": round(val, 4) for lab, val in v.items()} if isinstance(v, dict) else v
            print(f"t={t:>7}s  {shown}")
        return 0
    for item in run_rules(s, a.rules):
        spans = ", ".join(f"from {f['from_s']}s to {f['to_s'] if f['to_s'] is not None else 'the end'}" + ("" if f["to_s"] is None else "s") for f in item["fired"]) or "never"
        print(f"{item['alert']} (for {item['for']}, severity {item['severity'] or 'none'}): fired {spans}" + ("" if item["has_runbook"] else "  [no runbook_url annotation]"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
