"""The certificate, written for a person.

The certificate is the machine-readable record. This renders the part of it someone
needs in order to act: what was concluded, which values the first reading got wrong and
what they were corrected to, where the document itself does not hold, and what is left
for a person to look at.

It works from the certificate's JSON alone, so a report can be produced later from a
stored certificate without the document, the models or the run.

    from probity.report import render_report
    print(render_report(result.certificate.to_json()))
"""

from __future__ import annotations

from typing import Any

from .money import minor_units

_HEADLINE = {
    "CONFIRMED": "CONFIRMED: every rule passes on the final reading",
    "DOCUMENT_INCONSISTENT": "DOCUMENT INCONSISTENT: two readers agree on the reading, "
                             "and as read the document breaks a rule",
    "UNRESOLVED": "UNRESOLVED: a rule fails and the reading could not be confirmed; "
                  "a person has to look",
}


def _currency(cert: dict[str, Any]) -> str:
    for row in cert.get("rows", []):
        for f in row.get("fields", []):
            if f.get("currency"):
                return f["currency"]
    return ""


def _money(minor: int | None, exp: int) -> str:
    """Integer minor units to a printed figure, without passing through a float."""
    if minor is None:
        return ""
    sign, n = ("-" if minor < 0 else ""), abs(int(minor))
    if exp == 0:
        return f"{sign}{n:,}"
    whole, frac = divmod(n, 10 ** exp)
    return f"{sign}{whole:,}.{frac:0{exp}d}"


def _cell(text: Any) -> str:
    text = " ".join(str(text if text is not None else "").split())
    return text.replace("|", "\\|") or "(blank)"


def _models(cert: dict[str, Any]) -> tuple[dict[str, int], float]:
    calls: dict[str, int] = {}
    for c in cert.get("provenance", {}).get("model_calls", []):
        name = str(c.get("model", "")).removeprefix("llm:")
        calls[name] = calls.get(name, 0) + 1
    return calls, float(cert.get("provenance", {}).get("cost_usd") or 0.0)


def render_report(cert: dict[str, Any]) -> str:
    """A Markdown report for one document."""
    out = cert.get("outcome", {})
    conclusion = out.get("conclusion") or ("CONFIRMED" if out.get("accepted")
                                           else "UNRESOLVED")
    cur = _currency(cert)
    exp = minor_units(cur) if cur else 2
    inv = cert.get("invariants", {})
    corrections = cert.get("corrections", [])
    opinions = cert.get("second_opinions", [])
    calls, cost = _models(cert)
    pages = sorted({r.get("page") for r in cert.get("rows", []) if r.get("page")})

    lines = [f"# Verification report: {cert.get('document', {}).get('doc_id', '')}", "",
             f"**{_HEADLINE.get(conclusion, conclusion)}**", ""]
    if out.get("conclusion_reason"):
        lines += [f"Reason: {out['conclusion_reason']}.", ""]

    lines += ["| | |", "|---|---|",
              f"| Pages read | {len(pages)} |",
              f"| Rows read | {len(cert.get('rows', []))} |",
              f"| Rule checks passed | {inv.get('passed', 0)} of {inv.get('total', 0)} |",
              f"| Rows corrected | {len({c['row'] for c in corrections})} |"]
    for name, n in calls.items():
        lines.append(f"| Calls to `{name}` | {n} |")
    lines += [f"| Model cost | ${cost:.4f} |",
              f"| Document SHA-256 | `{cert.get('document', {}).get('sha256', '')[:16]}` |",
              ""]

    # ---------------------------------------------------------------- corrections
    lines += ["## Corrections", ""]
    if not corrections:
        lines += ["None. No value of the first reading was changed.", ""]
    else:
        by_second = [c for c in corrections if c.get("method", "second_reader") == "second_reader"]
        by_same = [c for c in corrections if c.get("method") == "same_reader_reread"]
        by_third = [c for c in corrections if c.get("method") == "third_reading"]
        if by_second:
            first, second = by_second[0]["first_reader"], by_second[0]["second_reader"]
            lines += [f"Values read by `{first}` on rows where a rule failed, read again "
                      f"independently by `{second}`, and replaced because the rule then "
                      f"passed and no other check failed. The rule selects the value; it "
                      f"does not prove what is printed.", ""]
        if by_third:
            lines += [f"{len({c['row'] for c in by_third})} row(s) marked *third reading* "
                      f"were first transcribed the same way by both models, and the rule "
                      f"failed. The first reader then transcribed the page again at a "
                      f"higher resolution, differently, and with that reading the rule "
                      f"passed. Both models had shared a misreading.", ""]
        if by_same:
            lines += [f"{len(by_same)} value(s) below were changed by the first reader "
                      f"re-reading the page itself, with no second reader behind them "
                      f"(marked *same reader*).", ""]
        lines += ["| Row | Page | Field | First reading | Changed to | Passing rules | By |",
                  "|---:|---:|---|---|---|---|---|"]
        for c in sorted(corrections, key=lambda c: (c["row"], c["field"])):
            who = {"second_reader": "second reader", "third_reading": "third reading",
                   "same_reader_reread": "same reader"}.get(
                       c.get("method", "second_reader"), "second reader")
            lines.append(f"| {c['row']} | {c['page']} | {c['field']} | "
                         f"{_cell(c['first_reading'])} | {_cell(c['corrected'])} | "
                         f"{', '.join(c.get('confirmed_by', []))} | {who} |")
        lines.append("")

    # ---------------------------------------------------------- document findings
    all_failures = inv.get("failures", [])
    row_failures: dict[int, list[dict]] = {}
    for f in all_failures:
        loc = f.get("location", {})
        if loc.get("scope") == "row" and loc.get("row_index") is not None:
            row_failures.setdefault(loc["row_index"], []).append(f)
    other_failures = [f for f in all_failures if f.get("location", {}).get("scope") != "row"]

    # An opinion is shown as a finding about the document only if it is the latest
    # word on its row and the row is still failing. Earlier opinions on a row that was
    # later corrected are history, and are in the certificate.
    latest: dict[str, dict] = {}
    for o in opinions:
        latest[o["region"]] = o
    # The certificate lists the rows whose finding still stands on the final figures.
    still = set(out.get("inconsistent_rows") or [])
    standing = [o for o in latest.values()
                if o["finding"] == "DOCUMENT_INCONSISTENT"
                and int(o["region"].split(":")[1]) in row_failures
                and int(o["region"].split(":")[1]) in still]
    if conclusion != "DOCUMENT_INCONSISTENT":
        # Agreement on some rows does not make the document's conclusion; say so.
        pass
    lines += ["## Rows where both readers agree and a rule fails", ""]
    if not standing:
        lines += ["None.", ""]
    for o in standing:
        row = int(o["region"].split(":")[1])
        both = next((r for r in o.get("rows", []) if r["row"] == row), None)
        lines += [f"### Row {row}, page {o['page']}", ""]
        for f in row_failures.get(row, []):
            if f.get("invariant") == "ROW_BAL":
                op = f.get("operands", {})
                movement = (op.get("credit") or 0) - (op.get("debit") or 0)
                lines += ["```",
                          f"{'previous balance':<21}{_money(op.get('prev_balance'), exp):>16}",
                          f"{'movement':<21}{_money(movement, exp):>16}",
                          f"{'should read':<21}{_money(f.get('expected'), exp):>16}",
                          f"{'transcribed balance':<21}{_money(f.get('actual'), exp):>16}",
                          f"{'difference':<21}{_money(f.get('delta'), exp):>16}",
                          "```", ""]
            else:
                lines += [f"{f.get('invariant')}: {f.get('message')}", ""]
        if both:
            lines += ["| Reader | Date | Debit | Credit | Balance |", "|---|---|---|---|---|"]
            for who, key in zip(o.get("readers", ["first", "second"]), ("first", "second")):
                r = both[key]
                lines.append(f"| `{who}` | {_cell(r['date'])} | {_cell(r['debit'])} | "
                             f"{_cell(r['credit'])} | {_cell(r['balance'])} |")
            third = next((r for r in o.get("rows", [])
                          if r["row"] == row and "third" in r), None)
            if third:
                r = third["third"]
                lines.append(f"| third reading (first reader, higher resolution) | "
                             f"{_cell(r['date'])} | {_cell(r['debit'])} | "
                             f"{_cell(r['credit'])} | {_cell(r['balance'])} |")
            lines += ["", "Both readers transcribed the same figures here and the same "
                      "balance carried in"
                      + (", and a third reading has them too" if third and third.get("agree")
                         else "")
                      + ". As transcribed, the statement does not add up at this row.", ""]

    # ------------------------------------------------------------------ unresolved
    standing_rows = {int(o["region"].split(":")[1]) for o in standing}
    loose_rows = sorted(r for r in row_failures if r not in standing_rows)
    explained = (conclusion == "DOCUMENT_INCONSISTENT")
    loose_other = [] if explained else other_failures
    if loose_rows or loose_other:
        lines += ["## For a person to check", ""]
        for r in loose_rows:
            o = latest.get(f"row:{r}")
            for f in row_failures[r]:
                lines.append(f"- row {r}, page {f['location'].get('page')}, "
                             f"{f.get('invariant')}: {f.get('message')}")
            if o:
                lines.append(f"  - second look ({o['finding']}): {o['reason']}")
                for v in o.get("rows", []):
                    if v["row"] == r and not v.get("agree") and "second" in v:
                        x, y = v["first"], v["second"]
                        lines.append(
                            f"  - first reader {_cell(x['date'])} / {_cell(x['debit'])} / "
                            f"{_cell(x['credit'])} / {_cell(x['balance'])}; second reader "
                            f"{_cell(y['date'])} / {_cell(y['debit'])} / {_cell(y['credit'])} "
                            f"/ {_cell(y['balance'])} (date / debit / credit / balance)")
        for f in loose_other:
            lines.append(f"- {f.get('location', {}).get('scope', 'document')}, "
                         f"{f.get('invariant')}: {f.get('message')}")
        lines.append("")
    elif conclusion == "UNRESOLVED":
        lines += ["## For a person to check", "",
                  f"- {out.get('conclusion_reason') or out.get('meaning') or 'not confirmed'}",
                  ""]
    if explained and other_failures:
        lines += ["The closing total is off by exactly the amount the row(s) above are "
                  "off by, so it is the same finding and not a separate one.", ""]

    # ----------------------------------------------------------------------- rules
    lines += ["## Rules", "", "| Rule | Passed | Failed |", "|---|---:|---:|"]
    for name, n in inv.get("by_invariant", {}).items():
        lines.append(f"| {name} | {n.get('pass', 0)} | {n.get('fail', 0)} |")
    lines += ["", "## What this report does not establish", "",
              "- that the document is authentic, or that a corrected value is what is "
              "printed: the rules establish that the reading is consistent"]
    for nc in cert.get("not_claimed", []):
        lines.append(f"- {nc.get('description')}")
    lines.append("")
    return "\n".join(lines)
