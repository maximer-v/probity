"""Render the transition table as a diagram, so the picture is generated from the code.

Both renderers read :data:`probity.machine.TRANSITIONS` directly. If someone adds a
transition and forgets the documentation, the documentation updates itself, and
``tests/test_export.py`` fails if the README's diagram no longer matches.

Mermaid is the primary format, for one reason worth recording: GitHub renders
``stateDiagram-v2`` inline in a README and themes it for light and dark automatically,
*and* Stately Sketch (https://sketch.stately.ai/, no account needed) accepts the same
Mermaid text as input and turns it into an interactive simulator. One string, two uses.

XState v6 JSON is emitted as well because the format is now documented
(https://stately.ai/docs/xstate/v6/serialization) and gives Sketch richer guard
rendering. It is optional: nothing in the runtime reads it back, and XState v6 is still
beta, so it is a convenience, not a dependency. See docs/STATE_MACHINE.md.
"""

from __future__ import annotations

import json
from typing import Any

from .machine import TRANSITIONS, TERMINAL_MEANING, Machine, State, Transition


def to_mermaid(transitions: tuple[Transition, ...] = TRANSITIONS, *,
               initial: State = State.INGEST, with_notes: bool = True) -> str:
    """A ``stateDiagram-v2`` block.

    Deliberately colourless: GitHub themes Mermaid from the reader's colour mode, and
    hardcoded fills are the usual reason a diagram is unreadable in dark mode.
    """
    lines = ["stateDiagram-v2", f"    [*] --> {initial.value}"]
    for t in transitions:
        label = t.label().replace(":", " ")
        lines.append(f"    {t.source.value} --> {t.target.value}: {label}")
    for term in (State.ACCEPT, State.HUMAN_REVIEW, State.ERROR):
        lines.append(f"    {term.value} --> [*]")
    if with_notes:
        lines.append("    note right of VERIFY")
        lines.append("        Only deterministic predicates decide here.")
        lines.append("        A model's own confidence is logged, never asked.")
        lines.append("    end note")
    return "\n".join(lines)


def to_xstate(machine: Machine | None = None,
              transitions: tuple[Transition, ...] = TRANSITIONS) -> dict[str, Any]:
    """An XState v6 machine definition.

    Two details of that format matter and are easy to get wrong: ``target`` must be an
    object (``{"target": "X"}``), the bare-string shorthand is rejected; and guards are
    references of the shape ``{"type": name, "params": {}}`` (the v4 key ``cond`` was
    renamed to ``guard`` in v5).
    """
    guards = machine.guards if machine else None
    states: dict[str, Any] = {}
    for state in State:
        node: dict[str, Any] = {}
        if state.is_terminal:
            node["type"] = "final"
            node["description"] = TERMINAL_MEANING[state]
        on: dict[str, list[dict[str, Any]]] = {}
        for t in transitions:
            if t.source != state:
                continue
            branch: dict[str, Any] = {"target": t.target.value}
            if t.guard:
                branch["guard"] = {"type": t.guard, "params": {}}
            if t.description:
                branch["description"] = t.description
            on.setdefault(t.label(), []).append(branch)
        if on:
            node["on"] = on
        states[state.value] = node

    out: dict[str, Any] = {
        "id": machine.name if machine else "probity.verified_extraction",
        "initial": (machine.initial if machine else State.INGEST).value,
        "version": "1.0.0",
        "description": "probity: deterministic verdicts over non-deterministic proposers",
        "states": states,
    }
    if guards is not None:
        out["meta"] = {"guards": {n: guards.doc(n) for n in guards.names()}}
    return out


def to_dot(transitions: tuple[Transition, ...] = TRANSITIONS) -> str:
    """Graphviz DOT, for a checked-in SVG when a denser layout is wanted."""
    lines = ["digraph probity {", '  rankdir=TB;', '  node [shape=box, fontname="Helvetica"];']
    for state in State:
        shape = "doublecircle" if state.is_terminal else "box"
        lines.append(f'  {state.value} [shape={shape}];')
    for t in transitions:
        lines.append(f'  {t.source.value} -> {t.target.value} [label="{t.label()}"];')
    lines.append("}")
    return "\n".join(lines)


def to_markdown_table(machine: Machine) -> str:
    """The transition table itself, as documentation."""
    rows = ["| from | guard | to | meaning |", "|---|---|---|---|"]
    for t in machine.transitions:
        guard = f"`{t.guard}`" if t.guard else "_(fallback)_"
        rows.append(f"| {t.source.value} | {guard} | {t.target.value} | "
                    f"{t.description or t.event or ''} |")
    return "\n".join(rows)


def write_all(out_dir: str, machine: Machine) -> dict[str, str]:
    """Write every representation next to each other; returns the paths written."""
    from pathlib import Path

    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    written = {}
    (d / "state_machine.mmd").write_text(to_mermaid() + "\n", encoding="utf-8")
    written["mermaid"] = str(d / "state_machine.mmd")
    (d / "state_machine.xstate.json").write_text(
        json.dumps(to_xstate(machine), indent=2) + "\n", encoding="utf-8")
    written["xstate"] = str(d / "state_machine.xstate.json")
    (d / "state_machine.dot").write_text(to_dot() + "\n", encoding="utf-8")
    written["dot"] = str(d / "state_machine.dot")
    return written
