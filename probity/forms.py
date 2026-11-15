"""Forms: documents made of named fields and one or more tables of lines.

A bank statement is a long ledger with a running balance, and has its own machinery
(:mod:`probity.pipeline`). A receipt, an invoice or a payslip is a different shape: a
handful of totals and a short list of lines, tied together by sums. This module checks
that shape, and a document type is defined entirely in YAML:

    doc_type: receipt.example
    kind: form
    amounts: integer            # how printed amounts are read: integer | decimal
    fields:
      subtotal: {type: money, optional: true}
      total:    {type: money}
    tables:
      items:
        columns:
          name:  {type: text}
          price: {type: money}
    rules:
      - id: ITEMS_SUM_TO_SUBTOTAL
        when: subtotal is not None
        check: sum(items.price) == subtotal
      - id: LINE_AMOUNT
        for_each: items
        when: row.quantity is not None and row.unit_price is not None
        check: row.quantity * row.unit_price == row.price

The rules are formulas, evaluated with exact integer arithmetic by a small interpreter
that knows names, attribute access, arithmetic, comparisons, ``and``/``or``/``not``,
``is None`` and the functions ``sum``, ``len``, ``abs``, ``min`` and ``max``. Nothing
else is executable from a spec.

The procedure is the one used for statements, restated for this shape:

1. the first reader transcribes the document;
2. the rules are evaluated; if all pass, the document is CONFIRMED;
3. otherwise a different model transcribes it again, blind, and the two transcriptions
   are compared cell by cell. A cell on which they differ is taken from the second
   reading only if doing so removes a failure and creates none;
4. if a rule still fails and the two readings agree on every cell that rule uses, the
   first reader transcribes the document once more from an enlarged image as a
   tie-break, under the same test. If the rule still fails, the document is reported as
   INCONSISTENT at that rule;
5. anything else is UNRESOLVED.

As with statements, a rule passing shows that a reading is consistent, not that it is
what is printed.
"""

from __future__ import annotations

import ast
import copy
import json
import re
from dataclasses import dataclass, field as dc_field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Callable

CONFIRMED, INCONSISTENT, UNRESOLVED = "CONFIRMED", "DOCUMENT_INCONSISTENT", "UNRESOLVED"


# ------------------------------------------------------------------------- spec

@dataclass
class Rule:
    id: str
    check: str
    when: str | None = None
    for_each: str | None = None


@dataclass
class FormSpec:
    doc_type: str
    amounts: str
    fields: dict[str, dict[str, Any]]
    tables: dict[str, dict[str, dict[str, Any]]]
    rules: list[Rule]
    instruction: str = ""

    @classmethod
    def load(cls, path: str | Path) -> "FormSpec":
        import yaml

        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if raw.get("kind") != "form":
            raise ValueError(f"{path}: not a form spec (kind: form)")
        tables = {name: dict(t.get("columns") or {}) for name, t in (raw.get("tables") or {}).items()}
        rules = [Rule(id=r["id"], check=r["check"], when=r.get("when"),
                      for_each=r.get("for_each")) for r in raw.get("rules") or []]
        spec = cls(doc_type=raw["doc_type"], amounts=raw.get("amounts", "decimal"),
                   fields=dict(raw.get("fields") or {}), tables=tables, rules=rules,
                   instruction=str(raw.get("instruction") or ""))
        spec.validate()
        return spec

    def validate(self) -> None:
        if self.amounts not in ("integer", "decimal"):
            raise ValueError("amounts must be 'integer' or 'decimal'")
        names = set(self.fields) | set(self.tables)
        for rule in self.rules:
            if rule.for_each and rule.for_each not in self.tables:
                raise ValueError(f"rule {rule.id}: no table named {rule.for_each!r}")
            for text in filter(None, (rule.check, rule.when)):
                for name in names_used(text):
                    if name not in names and name != "row":
                        raise ValueError(f"rule {rule.id}: unknown name {name!r}")
        if len({r.id for r in self.rules}) != len(self.rules):
            raise ValueError("rule ids must be unique")


# ------------------------------------------------------------------- expressions

class _Missing(Exception):
    """An operand a formula needs was not read."""


def _sum(values):
    values = list(values)
    if any(v is None for v in values):
        raise _Missing()                 # a line whose amount was not read
    return sum(values)


_ALLOWED_FUNCS: dict[str, Callable] = {"sum": _sum, "len": len, "abs": abs,
                                       "min": min, "max": max}
_BIN = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b, ast.FloorDiv: lambda a, b: a // b}
_CMP = {ast.Eq: lambda a, b: a == b, ast.NotEq: lambda a, b: a != b,
        ast.Lt: lambda a, b: a < b, ast.LtE: lambda a, b: a <= b,
        ast.Gt: lambda a, b: a > b, ast.GtE: lambda a, b: a >= b,
        ast.Is: lambda a, b: a is b, ast.IsNot: lambda a, b: a is not b}


class FormulaError(ValueError):
    """A rule uses something the formula language does not have."""


def names_used(text: str) -> set[str]:
    return {n.id for n in ast.walk(ast.parse(text, mode="eval"))
            if isinstance(n, ast.Name) and n.id not in _ALLOWED_FUNCS}


def cells_used(text: str) -> set[tuple[str, str | None]]:
    """(name, column) pairs a formula reads: ("total", None), ("items", "price")."""
    out: set[tuple[str, str | None]] = set()
    tree = ast.parse(text, mode="eval")
    attributed = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
            out.add((n.value.id, n.attr))
            attributed.add(id(n.value))
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and id(n) not in attributed and n.id not in _ALLOWED_FUNCS:
            out.add((n.id, None))
    return out


def evaluate(text: str, env: dict[str, Any]) -> Any:
    """Evaluate one formula. Integer arithmetic only; an operand that is None is an error."""

    def ev(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant):
            if node.value is None or isinstance(node.value, (bool, int)):
                return node.value
            raise FormulaError(f"constant {node.value!r} is not allowed (integers only)")
        if isinstance(node, ast.Name):
            if node.id in env:
                return env[node.id]
            raise FormulaError(f"unknown name {node.id!r}")
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("_"):
                raise FormulaError(f"attribute {node.attr!r} is not allowed")
            base = ev(node.value)
            if isinstance(base, list):                    # table.column -> list of cells
                return [r.get(node.attr) for r in base]
            if isinstance(base, dict):                    # row.column
                return base.get(node.attr)
            raise FormulaError(f"cannot take .{node.attr} of that")
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
            a, b = ev(node.left), ev(node.right)
            if a is None or b is None:
                raise _Missing()
            return _BIN[type(node.op)](a, b)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.Not)):
            v = ev(node.operand)
            if isinstance(node.op, ast.Not):
                return not v
            if v is None:
                raise _Missing()
            return -v
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                result: Any = True
                for v in node.values:
                    result = ev(v)
                    if not result:
                        return result
                return result
            result = False
            for v in node.values:
                result = ev(v)
                if result:
                    return result
            return result
        if isinstance(node, ast.Compare):
            left = ev(node.left)
            for op, right_node in zip(node.ops, node.comparators):
                right = ev(right_node)
                if type(op) not in _CMP:
                    raise FormulaError("comparison not allowed")
                # Only `is None` / `is not None` may look at a missing value. Comparing
                # one with == is a rule that cannot be evaluated, not one that fails.
                if type(op) not in (ast.Is, ast.IsNot) and (left is None or right is None):
                    raise _Missing()
                if not _CMP[type(op)](left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in _ALLOWED_FUNCS and not node.keywords:
            return _ALLOWED_FUNCS[node.func.id](*[ev(a) for a in node.args])
        raise FormulaError(f"{type(node).__name__} is not part of the formula language")

    return ev(ast.parse(text, mode="eval"))


# ---------------------------------------------------------------------- reading

_CURRENCY = re.compile(r"^(?:rp\.?|idr|rs\.?|inr|usd|eur|\$|€|£)\s*|\s*(?:rp|idr|inr|usd|eur)$", re.I)
#: digits; optionally groups of three all joined by the same separator; optionally a
#: two-digit fraction after a separator.
_AMOUNT = re.compile(r"(?P<whole>\d{1,3}(?:(?P<g>[.,])\d{3}(?:(?P=g)\d{3})*)?|\d+)"
                     r"(?:(?P<d>[.,])(?P<frac>\d{2}))?")


def parse_money(raw: Any, amounts: str) -> int | None:
    """Printed amount to an exact integer. None if nothing is printed or it is unclear.

    The whole cell must be one well-formed number, optionally with a currency mark and
    a sign: thousands in groups of three joined by one kind of separator, an optional
    two-digit fraction after the other kind, and nothing left over. ``integer``
    currencies (rupiah, yen) are whole units, so the fraction, if printed, must be
    ``00``; ``decimal`` currencies are returned as an integer number of cents. Anything
    else ("1.5" as an integer amount, "1,2,3", "1,234.567", "12 or 34") is not a number
    this function is willing to guess at.
    """
    text = str(raw if raw is not None else "").strip()
    if not text:
        return None
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative, text = True, text[1:-1].strip()
    text = _CURRENCY.sub("", text).strip()
    if text[:1] in "-\u2212\u2013":
        negative, text = True, text[1:].strip()
    text = _CURRENCY.sub("", text).strip()
    m = _AMOUNT.fullmatch(text)
    if not m:
        return None
    group, dec, frac = m.group("g"), m.group("d"), m.group("frac")
    if group and dec and group == dec:
        return None                       # "1,234,56": the same mark cannot do both jobs
    whole = int(re.sub(r"[.,]", "", m.group("whole")))
    if amounts == "integer":
        if frac not in (None, "00"):
            return None
        value = whole
    else:
        value = whole * 100 + int(frac or 0)
    return -value if negative else value


def parse_number(raw: Any) -> int | None:
    text = str(raw if raw is not None else "").strip().lower().rstrip("x").strip()
    text = text.replace(",", "").replace(".00", "")
    return int(text) if re.fullmatch(r"-?\d+", text) else None


def _typed(raw: Any, kind: str, amounts: str) -> Any:
    if raw is None or str(raw).strip() == "":
        return None
    if kind == "money":
        return parse_money(raw, amounts)
    if kind == "number":
        return parse_number(raw)
    return " ".join(str(raw).split())


@dataclass
class Reading:
    """One transcription: the characters as returned, and the values parsed from them."""

    fields: dict[str, Any] = dc_field(default_factory=dict)
    tables: dict[str, list[dict[str, Any]]] = dc_field(default_factory=dict)
    raw: dict[str, Any] = dc_field(default_factory=dict)
    reader: str = ""
    cost_usd: float = 0.0
    error: str = ""

    def env(self) -> dict[str, Any]:
        return {**self.fields, **self.tables}


def build_reading(data: dict[str, Any] | None, spec: FormSpec, reader: str = "",
                  cost: float = 0.0) -> Reading:
    if not isinstance(data, dict):
        return Reading(reader=reader, cost_usd=cost, error="the reader returned no usable JSON")
    out = Reading(reader=reader, cost_usd=cost, raw=data)
    for name, meta in spec.fields.items():
        out.fields[name] = _typed(data.get(name), meta.get("type", "text"), spec.amounts)
    for table, columns in spec.tables.items():
        rows = data.get(table) if isinstance(data.get(table), list) else []
        out.tables[table] = [
            {c: _typed(r.get(c), m.get("type", "text"), spec.amounts)
             for c, m in columns.items()}
            for r in rows if isinstance(r, dict)]
    return out


def schema_for(spec: FormSpec) -> dict[str, Any]:
    """The JSON shape a reader is asked for: every cell as the characters printed."""
    cell = {"type": ["string", "null"]}
    props: dict[str, Any] = {name: cell for name in spec.fields}
    for table, columns in spec.tables.items():
        props[table] = {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": list(columns), "properties": {c: cell for c in columns}}}
    return {"name": "form_transcription", "schema": {
        "type": "object", "additionalProperties": False,
        "required": list(props), "properties": props}}


def instruction_for(spec: FormSpec) -> str:
    lines = ["Transcribe this document into JSON.",
             "Copy every value exactly as it is printed, as a string, including separators.",
             "Use null for anything that is not printed. Do not compute, complete or "
             "correct anything.", "", "Fields:"]
    for name, meta in spec.fields.items():
        lines.append(f"- {name}: {meta.get('label', name)}")
    for table, columns in spec.tables.items():
        lines.append(f"Table `{table}`, one entry per printed line, in order:")
        for c, meta in columns.items():
            lines.append(f"- {c}: {meta.get('label', c)}")
    if spec.instruction:
        lines += ["", spec.instruction.strip()]
    lines += ["", "Reply with a single JSON object."]
    return "\n".join(lines)


class FormReader:
    """A vision model that transcribes a form. ``scale`` enlarges the image it is sent."""

    def __init__(self, client, model, scale: float = 1.0):
        self.client, self.model, self.scale = client, model, scale

    @property
    def name(self) -> str:
        return self.model.model

    def read(self, image_path: str, spec: FormSpec, purpose: str = "transcribe") -> Reading:
        from .openrouter import OUTPUT_CEILING, image_message
        from .proposers.vlm import _parse

        path = image_path
        if self.scale != 1.0:
            path = _scaled(image_path, self.scale)
        try:
            resp = self.client.chat(self.model, image_message(instruction_for(spec), [path]),
                                    json_schema=schema_for(spec), max_tokens=OUTPUT_CEILING,
                                    purpose=purpose)
        except Exception as exc:  # noqa: BLE001 - a failed call is a reading with an error
            return Reading(reader=self.name, error=f"{type(exc).__name__}: {exc}")
        if (resp.finish_reason or "").lower() in {"length", "max_tokens", "error"}:
            return Reading(reader=self.name, cost_usd=resp.cost_usd,
                           error=f"reply ended with {resp.finish_reason}")
        return build_reading(_parse(resp.text or ""), spec, self.name, resp.cost_usd)


def _scaled(image_path: str, scale: float) -> str:
    import hashlib
    import tempfile

    from PIL import Image

    src = Path(image_path).resolve()
    key = hashlib.sha256(f"{src}|{src.stat().st_size}|{scale}".encode()).hexdigest()[:16]
    out = Path(tempfile.gettempdir()) / "probity-pages" / f"{key}{src.suffix or '.png'}"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(src) as im:
            im = im.convert("RGB")
            im.resize((int(im.width * scale), int(im.height * scale)),
                      Image.LANCZOS).save(out)
    return str(out)


# ------------------------------------------------------------------------ rules

@dataclass
class Failure:
    rule: str
    row: int | None = None            # index in the table, for a for_each rule
    table: str | None = None
    reason: str = "does not hold"

    def key(self) -> tuple:
        return (self.rule, self.table, self.row)

    def to_json(self) -> dict[str, Any]:
        return {"rule": self.rule, "table": self.table, "row": self.row, "reason": self.reason}


NOT_READ = "a value it needs was not read"


def evaluate_rules(reading: Reading, spec: FormSpec) -> tuple[list[Failure], set[tuple]]:
    """Evaluate every rule. Returns the failures, and the keys of the rules that applied.

    A rule whose ``when`` is false does not apply. Which rules apply is returned too,
    because a "correction" that makes a failing rule stop applying (by blanking a value
    its ``when`` tests, or by dropping a line) has not satisfied it.
    """
    out: list[Failure] = []
    applied: set[tuple] = set()
    env = reading.env()
    for rule in spec.rules:
        scopes = ([(i, {**env, "row": r}) for i, r in enumerate(env.get(rule.for_each, []))]
                  if rule.for_each else [(None, env)])
        for index, scope in scopes:
            try:
                if rule.when and not evaluate(rule.when, scope):
                    continue
                applied.add((rule.id, rule.for_each, index))
                ok = bool(evaluate(rule.check, scope))
                reason = "does not hold"
            except _Missing:
                applied.add((rule.id, rule.for_each, index))
                ok, reason = False, NOT_READ
            if not ok:
                out.append(Failure(rule.id, index, rule.for_each, reason))
    return out, applied


def check(reading: Reading, spec: FormSpec) -> list[Failure]:
    return evaluate_rules(reading, spec)[0]


def rule_cells(spec: FormSpec, failure: Failure) -> set[tuple[str, str | None, int | None]]:
    """The cells a failing rule reads: (name, column, row). Row None means every row."""
    rule = next(r for r in spec.rules if r.id == failure.rule)
    out: set[tuple[str, str | None, int | None]] = set()
    for text in filter(None, (rule.check, rule.when)):
        for name, column in cells_used(text):
            if name == "row":
                out.add((rule.for_each or "", column, failure.row))
            else:
                out.add((name, column, None))
    return out


# -------------------------------------------------------------------- comparing

def _norm(text: Any) -> str:
    return " ".join(str(text or "").lower().split())


def _digits(text: Any) -> str:
    return "".join(ch for ch in str(text or "") if ch.isdigit())


def _same_line(a: str, b: str) -> bool:
    """Do two transcribed line texts name the same line?

    Only if they are identical once case, spacing and punctuation are set aside. Close
    is not enough: "COFFEE LARGE A" and "COFFEE LARGE B" are different lines, and a
    one-character difference is exactly what separates neighbours on a receipt. The
    price is that a line whose text one reader got slightly wrong cannot be matched,
    and stays unresolved.
    """
    key = lambda t: "".join(ch for ch in _norm(t) if ch.isalnum())  # noqa: E731
    return bool(key(a)) and key(a) == key(b)


def align_rows(first: list[dict], second: list[dict], columns: dict[str, dict]) -> dict[int, int]:
    """Pair the lines of two transcriptions of one table. first index -> second index.

    A line is paired with the line whose text names the same line (see
    :func:`_same_line`), and only if that match is unique in both directions. Lines are
    never paired by position alone: two readers that list the same lines in a different
    order, or that each dropped a different line, would otherwise have a value moved
    from one line to another.
    """
    text_cols = [c for c, m in columns.items() if m.get("type", "text") == "text"]

    def text(r): return " ".join(str(r.get(c) or "") for c in text_cols)

    pairs: dict[int, int] = {}
    for i, a in enumerate(first):
        matches = [j for j, b in enumerate(second) if _same_line(text(a), text(b))]
        if len(matches) != 1:
            continue
        j = matches[0]
        back = [k for k, c in enumerate(first) if _same_line(text(c), text(second[j]))]
        if back == [i]:
            pairs[i] = j
    return pairs


def differences(a: Reading, b: Reading, spec: FormSpec,
                include_text: bool = False) -> list[dict[str, Any]]:
    """Every cell on which two readings differ, as edits that would turn ``a`` into ``b``.

    Text cells are compared only when ``include_text`` is set: they are never corrected
    from another reading, but they do count when asking whether two readers agree.
    """
    out: list[dict[str, Any]] = []
    for name, meta in spec.fields.items():
        is_text = meta.get("type", "text") == "text"
        if is_text and not include_text:
            continue
        va, vb = a.fields.get(name), b.fields.get(name)
        if (_norm(va) != _norm(vb)) if is_text else (va != vb):
            out.append({"where": name, "table": None, "row": None, "column": None,
                        "first": va, "second": vb, "text": is_text})
    for table, columns in spec.tables.items():
        ra, rb = a.tables.get(table, []), b.tables.get(table, [])
        pairs = align_rows(ra, rb, columns)
        for i, j in pairs.items():
            for c, meta in columns.items():
                is_text = meta.get("type", "text") == "text"
                if is_text and not include_text:
                    continue
                va, vb = ra[i].get(c), rb[j].get(c)
                if (_norm(va) != _norm(vb)) if is_text else (va != vb):
                    out.append({"where": f"{table}[{i}].{c}", "table": table, "row": i,
                                "column": c, "first": va, "second": vb, "text": is_text})
        if len(ra) != len(rb) or len(pairs) != len(ra):
            out.append({"where": f"{table} (lines)", "table": table, "row": None,
                        "column": None, "first": len(ra), "second": len(rb),
                        "unpaired": True})
    return out


def _apply(reading: Reading, edits: list[dict[str, Any]]) -> Reading:
    new = copy.deepcopy(reading)
    for edit in edits:
        if edit["table"] is None:
            new.fields[edit["where"]] = edit["second"]
        else:
            new.tables[edit["table"]][edit["row"]][edit["column"]] = edit["second"]
    return new


def reconcile(current: Reading, other: Reading, spec: FormSpec, method: str,
              corrections: list[dict[str, Any]]) -> Reading:
    """Take values from ``other`` while each step removes a failure and costs nothing.

    A step is one cell, or all the differing cells of one line together (a quantity and
    a unit price are often misread as a pair), or every differing cell at once. A step
    is accepted only if, afterwards:

    * the failing rules are a strict subset of those failing before;
    * every rule that applied before still applies, so a rule cannot be "satisfied" by
      blanking the value that switches it on;
    * no value that had been read is replaced by nothing.

    Lines are never added, removed or reordered: only cells of lines that the two
    readings both have, matched by their text, can change.
    """
    progress = True
    while progress:
        progress = False
        before_failures, before_applied = evaluate_rules(current, spec)
        before = {f.key() for f in before_failures}
        if not before:
            break
        edits = [e for e in differences(current, other, spec)
                 if not e.get("unpaired") and not e.get("text")
                 and not (e["first"] is not None and e["second"] is None)]
        by_row: dict[tuple, list[dict]] = {}
        for e in edits:
            if e["row"] is not None:
                by_row.setdefault((e["table"], e["row"]), []).append(e)
        steps = [[e] for e in edits] + [g for g in by_row.values() if len(g) > 1]
        if len(edits) > 1:
            steps.append(edits)
        for step in steps:
            trial = _apply(current, step)
            after_failures, after_applied = evaluate_rules(trial, spec)
            after = {f.key() for f in after_failures}
            if after < before and before_applied <= after_applied:
                for edit in step:
                    corrections.append({
                        "where": edit["where"], "first_reading": edit["first"],
                        "corrected": edit["second"], "method": method,
                        "first_reader": current.reader, "second_reader": other.reader,
                        "failures_before": len(before), "failures_after": len(after)})
                current = trial
                progress = True
                break
    return current


def _agree_on(a: Reading, b: Reading, spec: FormSpec, failures: list[Failure]) -> bool:
    """Do two readings independently hold the same value in every cell the failing rules read?

    Text cells count. So does the shape of a table a rule sums over: if the readings
    disagree on which lines exist, they do not agree on the sum.
    """
    diffs = differences(a, b, spec, include_text=True)
    needed: set[tuple[str, str | None, int | None]] = set()
    for f in failures:
        needed |= rule_cells(spec, f)
    for d in diffs:
        for name, column, row in needed:
            if d["table"] is None and d["where"] == name:
                return False
            if d["table"] == name and d.get("unpaired"):
                return False
            if d["table"] == name and (column is None or d["column"] == column) \
                    and (row is None or d["row"] == row):
                return False
    return True


# --------------------------------------------------------------------- pipeline

@dataclass
class FormResult:
    doc_id: str
    conclusion: str
    reason: str
    reading: Reading
    failures: list[Failure]
    corrections: list[dict[str, Any]]
    readings: list[Reading]
    steps: list[str]

    @property
    def cost_usd(self) -> float:
        return sum(r.cost_usd for r in self.readings)

    def to_json(self) -> dict[str, Any]:
        return {"doc_id": self.doc_id, "conclusion": self.conclusion, "reason": self.reason,
                "fields": self.reading.fields, "tables": self.reading.tables,
                "failures": [f.to_json() for f in self.failures],
                "corrections": self.corrections, "steps": self.steps,
                "readers": [r.reader for r in self.readings],
                "cost_usd": round(self.cost_usd, 6)}


class FormPipeline:
    """Read, check, read again where a rule fails, compare, conclude."""

    def __init__(self, spec: FormSpec, reader, second=None, tiebreak=None):
        self.spec, self.reader, self.second, self.tiebreak = spec, reader, second, tiebreak
        if second is not None and getattr(second, "name", "b") == getattr(reader, "name", "a"):
            raise ValueError("the second reader must be a different model from the first")

    def run(self, doc_id: str, image_path: str) -> FormResult:
        spec, steps, corrections = self.spec, [], []
        first = self.reader.read(image_path, spec)
        readings = [first]
        if first.error:
            return FormResult(doc_id, UNRESOLVED, f"the document could not be read: "
                              f"{first.error}", first, [], corrections, readings, steps)
        current = first
        failures = check(current, spec)
        steps.append(f"first reading: {len(failures)} rule failure(s)")
        if not failures:
            return FormResult(doc_id, CONFIRMED, "every rule passed", current, [],
                              corrections, readings, steps)
        if self.second is None:
            return FormResult(doc_id, UNRESOLVED, "a rule fails and no second reader is "
                              "configured", current, failures, corrections, readings, steps)

        second = self.second.read(image_path, spec, purpose="second_opinion")
        readings.append(second)
        if second.error:
            return FormResult(doc_id, UNRESOLVED, f"a rule fails and the second reading "
                              f"was not obtained: {second.error}", current, failures,
                              corrections, readings, steps)
        current = reconcile(current, second, spec, "second_reader", corrections)
        failures = check(current, spec)
        steps.append(f"after the second reading: {len(failures)} failure(s), "
                     f"{len(corrections)} cell(s) corrected")
        if not failures:
            return FormResult(doc_id, CONFIRMED, f"every rule passed; "
                              f"{len(corrections)} cell(s) were corrected on the way",
                              current, [], corrections, readings, steps)

        # A rule that fails because a value was not read says nothing about the
        # document, whether or not both readers missed it.
        if any(f.reason == NOT_READ for f in failures):
            return FormResult(doc_id, UNRESOLVED, "a rule cannot be evaluated because a "
                              "value it needs was not read", current, failures,
                              corrections, readings, steps)
        # Agreement is judged on what each reader independently transcribed.
        if not _agree_on(first, second, spec, failures):
            return FormResult(doc_id, UNRESOLVED, "a rule fails, and the two readers "
                              "disagree on a value it uses without either reading "
                              "satisfying it", current, failures, corrections, readings, steps)

        if self.tiebreak is not None:
            third = self.tiebreak.read(image_path, spec, purpose="reread")
            readings.append(third)
            if not third.error:
                before = len(corrections)
                current = reconcile(current, third, spec, "third_reading", corrections)
                failures = check(current, spec)
                steps.append(f"after the third reading: {len(failures)} failure(s), "
                             f"{len(corrections) - before} cell(s) corrected")
                if not failures:
                    return FormResult(doc_id, CONFIRMED, "every rule passed; a third "
                                      "reading corrected a value both readers had shared",
                                      current, [], corrections, readings, steps)
                if len(corrections) > before:
                    return FormResult(doc_id, UNRESOLVED, "a third reading changed a "
                                      "value and a rule still fails", current, failures,
                                      corrections, readings, steps)
        where = ", ".join(sorted({f.rule + (f"[{f.row}]" if f.row is not None else "")
                                  for f in failures}))
        return FormResult(doc_id, INCONSISTENT, f"two readers agree on every value these "
                          f"rules use, and they do not hold: {where}", current, failures,
                          corrections, readings, steps)


def render_report(result: FormResult, spec: FormSpec) -> str:
    """The result, for a person."""
    lines = [f"# Verification report: {result.doc_id}", "", f"**{result.conclusion}**", "",
             f"Reason: {result.reason}.", "", "## Reading", "", "| Field | Value |", "|---|---|"]
    for name in spec.fields:
        lines.append(f"| {name} | {result.reading.fields.get(name)} |")
    for table, columns in spec.tables.items():
        lines += ["", f"### {table}", "", "| # | " + " | ".join(columns) + " |",
                  "|---:|" + "---|" * len(columns)]
        for i, row in enumerate(result.reading.tables.get(table, [])):
            lines.append(f"| {i} | " + " | ".join(str(row.get(c)) for c in columns) + " |")
    lines += ["", "## Corrections", ""]
    if not result.corrections:
        lines.append("None.")
    else:
        lines += ["| Where | First reading | Changed to | By |", "|---|---|---|---|"]
        for c in result.corrections:
            lines.append(f"| {c['where']} | {c['first_reading']} | {c['corrected']} | "
                         f"{c['method'].replace('_', ' ')} |")
    lines += ["", "## Rules that do not hold", ""]
    if not result.failures:
        lines.append("None.")
    for f in result.failures:
        rule = next(r for r in spec.rules if r.id == f.rule)
        at = f" at {f.table}[{f.row}]" if f.row is not None else ""
        lines.append(f"- `{f.rule}`{at}: `{rule.check}` {f.reason}")
    lines += ["", "## Steps", ""] + [f"- {s}" for s in result.steps]
    return "\n".join(lines) + "\n"


def dumps(result: FormResult) -> str:
    return json.dumps(result.to_json(), indent=1, ensure_ascii=False)
