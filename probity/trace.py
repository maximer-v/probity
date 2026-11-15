"""The trace: a complete, replayable record of why the machine did what it did.

Most pipelines log what happened. This one logs *what was asked and what each answer
was*, which is a different thing. When a document lands in HUMAN_REVIEW the trace already
contains the arithmetic that failed, the guards that were consulted and declined, the
budget that ran out, and the exact bytes of every model call, so nobody has to re-run the
document to find out what went wrong.

Three readers are served by the same event stream:

``to_jsonl()``   one JSON object per event, for machines and for diffing two runs
``explain()``    an indented, human report: step, question, answer, evidence
``replay_hash()``  a hash over only the deterministic fields, so two runs can be
                 compared for identity without timestamps and durations spoiling it
"""

from __future__ import annotations

import enum
import hashlib
import json
import time
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any, Iterable

from .machine import State


class EventKind(enum.StrEnum):
    RUN_START = "run_start"
    STATE_ENTER = "state_enter"
    GUARD = "guard"                 # one guard asked, with its answer and its evidence
    TRANSITION = "transition"
    EXTRACTION = "extraction"       # a proposer returned a candidate
    INVARIANT = "invariant"         # the full verification report for one pass
    GROUNDING = "grounding"
    REPAIR_ATTEMPT = "repair_attempt"
    TIER_CHANGE = "tier_change"
    MODEL_CALL = "model_call"
    BUDGET = "budget"
    NOTE = "note"
    RUN_END = "run_end"


# Fields excluded from the replay hash because they vary between identical runs.
_NONDETERMINISTIC = {"wall_ms", "ts", "latency_ms", "provider_latency_ms", "seq_ms"}


def _strip(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _strip(v) for k, v in value.items() if k not in _NONDETERMINISTIC}
    if isinstance(value, list):
        return [_strip(v) for v in value]
    return value


@dataclass
class Event:
    seq: int
    kind: EventKind
    state: State | None
    message: str
    data: dict[str, Any] = dc_field(default_factory=dict)
    wall_ms: float = 0.0

    def to_json(self) -> dict[str, Any]:
        return {"seq": self.seq, "kind": str(self.kind),
                "state": str(self.state) if self.state else None,
                "message": self.message, "wall_ms": round(self.wall_ms, 1), **self.data}

    def deterministic_json(self) -> dict[str, Any]:
        """The event with every nondeterministic field removed, at any depth.

        Stripping only the top level left `latency_ms` nested inside a model-call
        record, so two identical runs that differed solely in timing produced different
        replay hashes and the reproducibility metric measured the clock.
        """
        return _strip(self.to_json())


@dataclass
class ModelCall:
    """Everything needed to audit, price and reproduce one model call (P8).

    The prompt and the output are stored as hashes by default: a bank statement is
    personal data, and a log that quotes it is a second copy of it. ``keep_text``
    switches to storing the text, for synthetic benchmark runs where that is useful.
    """

    tier: str
    model: str
    provider: str | None = None
    params: dict[str, Any] = dc_field(default_factory=dict)
    prompt_sha256: str = ""
    output_sha256: str = ""
    prompt_text: str | None = None
    output_text: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    cached: bool = False
    error: str | None = None
    purpose: str = ""           # "structure" | "retranscribe_region" | "classify"
    region: str | None = None

    def to_json(self) -> dict[str, Any]:
        out = {
            "tier": self.tier, "model": self.model, "provider": self.provider,
            "params": self.params, "prompt_sha256": self.prompt_sha256[:16],
            "output_sha256": self.output_sha256[:16],
            "prompt_tokens": self.prompt_tokens, "completion_tokens": self.completion_tokens,
            "cost_usd": round(self.cost_usd, 6), "latency_ms": round(self.latency_ms, 1),
            "cached": self.cached, "error": self.error, "purpose": self.purpose,
            "region": self.region,
        }
        if self.prompt_text is not None:
            out["prompt_text"] = self.prompt_text
        if self.output_text is not None:
            out["output_text"] = self.output_text
        return out


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class Trace:
    doc_id: str
    spec_fingerprint: str = ""
    framework_version: str = ""
    events: list[Event] = dc_field(default_factory=list)
    model_calls: list[ModelCall] = dc_field(default_factory=list)
    keep_model_text: bool = False
    _t0: float = dc_field(default_factory=time.perf_counter)

    # ---------------------------------------------------------------- recording

    def _add(self, kind: EventKind, state: State | None, message: str, **data) -> Event:
        ev = Event(len(self.events), kind, state, message, data,
                   (time.perf_counter() - self._t0) * 1000)
        self.events.append(ev)
        return ev

    def run_start(self, **data) -> None:
        self._add(EventKind.RUN_START, None, f"processing {self.doc_id}",
                  spec=self.spec_fingerprint, version=self.framework_version, **data)

    def state_enter(self, state: State, **data) -> None:
        self._add(EventKind.STATE_ENTER, state, f"entering {state}", **data)

    def guard(self, state: State, name: str, answer: bool, why: str = "", **evidence) -> None:
        """A guard was asked. Record the answer *and* the evidence behind it.

        Guards that answered no are as informative as the one that answered yes: they
        are the record of the options the machine considered and ruled out.
        """
        self._add(EventKind.GUARD, state, f"{name} -> {answer}",
                  guard=name, answer=answer, why=why, evidence=evidence or None)

    def transition(self, src: State, dst: State, via: str, asked: list[tuple[str, bool]]) -> None:
        self._add(EventKind.TRANSITION, src, f"{src} -> {dst} via {via or 'fallback'}",
                  **{"from": str(src), "to": str(dst), "via": via or "fallback",
                     "guards_asked": [{"guard": g, "answer": a} for g, a in asked]})

    def extraction(self, tier: str, rows: int, fields_failed: int, codes: dict[str, int],
                   region: str | None = None, **data) -> None:
        self._add(EventKind.EXTRACTION, State.EXTRACT,
                  f"{tier} proposed {rows} rows, {fields_failed} unreadable cells",
                  tier=tier, rows=rows, fields_failed=fields_failed,
                  parse_error_codes=codes, region=region, **data)

    def invariants(self, report, **data) -> None:
        self._add(EventKind.INVARIANT, State.VERIFY,
                  report.explain(limit=6), report=report.to_json(), **data)

    def grounding(self, report, **data) -> None:
        self._add(EventKind.GROUNDING, State.GROUND, report.explain(limit=6),
                  report=report.to_json(), **data)

    def repair(self, region: str, strategy: str, outcome: str, detail: dict | None = None) -> None:
        self._add(EventKind.REPAIR_ATTEMPT, State.REPAIR,
                  f"{region}: {strategy} -> {outcome}",
                  region=region, strategy=strategy, outcome=outcome, detail=detail)

    def tier_change(self, old: str, new: str, reason: str, region: str | None = None) -> None:
        self._add(EventKind.TIER_CHANGE, State.ESCALATE_TIER,
                  f"{old} -> {new} ({reason})", old_tier=old, new_tier=new,
                  reason=reason, region=region)

    def model_call(self, call: ModelCall) -> None:
        if not self.keep_model_text:
            call.prompt_text = None
            call.output_text = None
        self.model_calls.append(call)
        self._add(EventKind.MODEL_CALL, None,
                  f"{call.model} ({call.purpose}) "
                  f"{'cached' if call.cached else f'${call.cost_usd:.5f}'}"
                  + (f" ERROR {call.error}" if call.error else ""),
                  call=call.to_json())

    def budget(self, kind: str, spent: float, limit: float, blocked: bool = False) -> None:
        self._add(EventKind.BUDGET, None,
                  f"{kind} {spent:g}/{limit:g}" + (" EXHAUSTED" if blocked else ""),
                  budget_kind=kind, spent=spent, limit=limit, blocked=blocked)

    def note(self, message: str, **data) -> None:
        self._add(EventKind.NOTE, None, message, **data)

    def run_end(self, final: State, **data) -> None:
        self._add(EventKind.RUN_END, final, f"finished in {final}",
                  final_state=str(final), total_cost_usd=round(self.total_cost(), 6),
                  model_calls=len(self.model_calls), **data)

    # ------------------------------------------------------------------ reading

    def total_cost(self) -> float:
        return sum(c.cost_usd for c in self.model_calls)

    def of_kind(self, kind: EventKind) -> list[Event]:
        return [e for e in self.events if e.kind is kind]

    def path(self) -> list[str]:
        return [e.data["to"] for e in self.of_kind(EventKind.TRANSITION)]

    def final_state(self) -> State | None:
        ends = self.of_kind(EventKind.RUN_END)
        return State(ends[-1].data["final_state"]) if ends else None

    def to_jsonl(self) -> str:
        return "\n".join(json.dumps(e.to_json(), default=str, separators=(",", ":"))
                         for e in self.events)

    def write(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.to_jsonl() + "\n", encoding="utf-8")

    def replay_hash(self) -> str:
        """Hash of the deterministic part of the run.

        Two runs of the same document with the same configuration and the same cached
        model responses must produce the same value. When they do not, the trace diff
        shows the first event where they parted.
        """
        payload = json.dumps([e.deterministic_json() for e in self.events],
                             sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()

    # -------------------------------------------------------------- the report

    def explain(self, *, verbose: bool = True) -> str:
        """The failure forensics, as prose. This is what a human reads first."""
        lines = [f"=== {self.doc_id} ===",
                 f"spec {self.spec_fingerprint}  probity {self.framework_version}"]
        indent = "  "
        for ev in self.events:
            if ev.kind is EventKind.STATE_ENTER:
                lines.append(f"\n{ev.data.get('state', ev.state)}")
            elif ev.kind is EventKind.GUARD:
                mark = "yes" if ev.data["answer"] else "no "
                why = f"  <- {ev.data['why']}" if ev.data.get("why") else ""
                lines.append(f"{indent}ask  {ev.data['guard']:<28} {mark}{why}")
            elif ev.kind is EventKind.TRANSITION:
                lines.append(f"{indent}go   {ev.data['from']} -> {ev.data['to']} "
                             f"(via {ev.data['via']})")
            elif ev.kind is EventKind.EXTRACTION:
                lines.append(f"{indent}read {ev.message}")
                codes = ev.data.get("parse_error_codes") or {}
                if codes and verbose:
                    for code, n in sorted(codes.items()):
                        lines.append(f"{indent}       unreadable: {code} x{n}")
            elif ev.kind is EventKind.INVARIANT:
                for line in ev.message.split("\n"):
                    lines.append(f"{indent}chk  {line}")
            elif ev.kind is EventKind.GROUNDING:
                for line in ev.message.split("\n"):
                    lines.append(f"{indent}gnd  {line}")
            elif ev.kind is EventKind.REPAIR_ATTEMPT:
                lines.append(f"{indent}fix  {ev.message}")
            elif ev.kind is EventKind.TIER_CHANGE:
                lines.append(f"{indent}tier {ev.message}")
            elif ev.kind is EventKind.MODEL_CALL and verbose:
                lines.append(f"{indent}call {ev.message}")
            elif ev.kind is EventKind.BUDGET and ev.data.get("blocked"):
                lines.append(f"{indent}stop {ev.message}")
            elif ev.kind is EventKind.NOTE:
                lines.append(f"{indent}note {ev.message}")
            elif ev.kind is EventKind.RUN_END:
                lines.append(f"\nFINAL {ev.data['final_state']}: "
                             f"{ev.data.get('reason', '')}".rstrip(": "))
                lines.append(f"{indent}{ev.data['model_calls']} model call(s), "
                             f"${ev.data['total_cost_usd']:.5f}, "
                             f"{ev.wall_ms:.0f} ms")
        return "\n".join(lines)

    def first_failure(self) -> dict[str, Any] | None:
        """The earliest thing that went wrong, for a one-line summary in a table."""
        for ev in self.events:
            if ev.kind is EventKind.INVARIANT:
                rep = ev.data.get("report", {})
                if not rep.get("all_passed"):
                    fails = rep.get("results", [])
                    first = next((r for r in fails if not r["ok"]), None)
                    if first:
                        return {"stage": "VERIFY", "invariant": first["invariant"],
                                "code": first["code"], "location": first["location"],
                                "message": first["message"]}
            if ev.kind is EventKind.GROUNDING:
                rep = ev.data.get("report", {})
                if rep.get("failures"):
                    f = rep["failures"][0]
                    return {"stage": "GROUND", "code": f["code"], "field": f["field"],
                            "message": f["message"]}
            if ev.kind is EventKind.EXTRACTION and ev.data.get("rows", 0) == 0:
                return {"stage": "EXTRACT", "code": "NO_ROWS",
                        "message": f"{ev.data.get('tier')} returned no rows"}
        return None


def diff_traces(a: Trace, b: Trace, limit: int = 5) -> str:
    """Where two runs parted company. Used by the reproducibility metric."""
    if a.replay_hash() == b.replay_hash():
        return "identical"
    ea, eb = [e.deterministic_json() for e in a.events], [e.deterministic_json() for e in b.events]
    lines = []
    for i in range(max(len(ea), len(eb))):
        x = ea[i] if i < len(ea) else None
        y = eb[i] if i < len(eb) else None
        if x != y:
            lines.append(f"  event {i}:\n    A: {json.dumps(x, default=str)[:300]}\n"
                         f"    B: {json.dumps(y, default=str)[:300]}")
            if len(lines) >= limit:
                break
    return f"diverged at {len(lines)} point(s):\n" + "\n".join(lines)


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]
