"""The table is the machine, and the diagram is the table."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from probity.export import to_dot, to_markdown_table, to_mermaid, to_xstate
from probity.machine import TRANSITIONS, GuardRegistry, Machine, State, build_machine
from probity.pipeline import build_guards


def test_machine_validates():
    build_machine(build_guards())


def test_every_non_terminal_state_has_an_unconditional_fallback():
    """Without this a document could reach a state and get stuck there."""
    m = build_machine(build_guards())
    for state in State:
        if state.is_terminal:
            continue
        outs = m.outgoing(state)
        assert outs, state
        assert outs[-1].guard == "", f"{state} ends with a guarded transition"


def test_unregistered_guard_is_rejected():
    from probity.machine import Transition

    reg = GuardRegistry()
    m = Machine("bad", State.INGEST,
                (Transition(State.INGEST, State.ACCEPT, "nope"),), reg)
    with pytest.raises(ValueError, match="unregistered guard"):
        m.validate()


def test_unreachable_state_is_rejected():
    from probity.machine import Transition

    reg = build_guards()
    m = Machine("bad", State.INGEST,
                (Transition(State.INGEST, State.ACCEPT, ""),), reg)
    with pytest.raises(ValueError, match="no outgoing transition|unreachable"):
        m.validate()


def test_first_matching_guard_wins_and_every_guard_asked_is_recorded():
    """Order in the table is priority, and the losers are part of the audit trail."""
    from probity.machine import Transition

    reg = GuardRegistry()
    reg.add("never", lambda ctx: False, "")
    reg.add("always", lambda ctx: True, "")
    m = Machine("t", State.VERIFY, (
        Transition(State.VERIFY, State.REPAIR, "never"),
        Transition(State.VERIFY, State.ACCEPT, "always"),
        Transition(State.VERIFY, State.HUMAN_REVIEW, ""),
    ), reg)
    t, asked = m.next_transition(State.VERIFY, None)
    assert t.target is State.ACCEPT
    assert asked == [("never", False), ("always", True)]


def test_no_confidence_guard_exists():
    """P4: routing is on verdicts. A confidence gate must not be reachable."""
    names = build_guards().names()
    assert not [n for n in names if "confidence" in n or "confident" in n]


# ------------------------------------------------------------------------ export

def test_mermaid_covers_every_transition():
    text = to_mermaid()
    assert text.startswith("stateDiagram-v2")
    for t in TRANSITIONS:
        assert f"{t.source.value} --> {t.target.value}" in text


def test_mermaid_has_no_hardcoded_colours():
    """GitHub themes Mermaid from the reader's colour mode; fixed fills break dark mode."""
    text = to_mermaid()
    for token in ("style ", "classDef", "fill:", "#"):
        assert token not in text, f"{token!r} would fix the theme"


def test_documented_diagram_matches_the_code():
    """The table in docs/STATE_MACHINE.md is generated; this fails if it drifts."""
    doc = Path(__file__).resolve().parents[1] / "docs" / "STATE_MACHINE.md"
    if not doc.exists():
        pytest.skip("docs not present")
    text = doc.read_text(encoding="utf-8")
    for t in TRANSITIONS:
        guard = f"`{t.guard}`" if t.guard else "_(fallback)_"
        row = f"| {t.source.value} | {guard} | {t.target.value} |"
        assert row in text, (
            f"docs/STATE_MACHINE.md is missing the row {row}; "
            "regenerate the table with probity.export.to_markdown_table")


def test_xstate_json_shape():
    """The v6 format rejects a bare-string target and renamed `cond` to `guard`."""
    m = build_machine(build_guards())
    data = to_xstate(m)
    assert data["initial"] == "INGEST"
    blob = json.dumps(data)
    assert '"cond"' not in blob
    for state, node in data["states"].items():
        for event, branches in (node.get("on") or {}).items():
            for b in branches:
                assert isinstance(b["target"], str)
                assert "target" in b
                if "guard" in b:
                    assert set(b["guard"]) == {"type", "params"}
    for terminal in ("ACCEPT", "HUMAN_REVIEW", "ERROR"):
        assert data["states"][terminal]["type"] == "final"


def test_xstate_json_is_serialisable():
    json.dumps(to_xstate(build_machine(build_guards())))


def test_dot_and_markdown_render():
    assert to_dot().startswith("digraph")
    table = to_markdown_table(build_machine(build_guards()))
    assert "| from | guard | to |" in table
    assert "ACCEPT" in table
