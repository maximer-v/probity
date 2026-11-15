"""The deterministic state machine: states as an enum, transitions as a table.

This is the part that must never surprise anyone. There is no agent loop, no planner and
no hidden control flow: a single `while` loop reads an ordered transition table, asks
each guard in turn, takes the first that answers yes, and records the answer of every
guard it asked — including the ones that said no — in the trace.

Because guards are deterministic functions of the context and the table is data, the same inputs
and the same cached model responses reproduce the same path, and the path can be replayed
from the log without re-running anything. That is the product feature; a library that
owns the loop for us would make it harder to prove, not easier.

The table is also the documentation: :mod:`probity.export` renders this exact object to
Mermaid and to XState JSON, so the diagram in the docs is generated, not drawn.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field as dc_field
from typing import Any, Callable


class State(enum.StrEnum):
    INGEST = "INGEST"
    CLASSIFY = "CLASSIFY"
    EXTRACT = "EXTRACT"
    GROUND = "GROUND"
    VERIFY = "VERIFY"
    REPAIR = "REPAIR"
    ESCALATE_TIER = "ESCALATE_TIER"
    ACCEPT = "ACCEPT"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    ERROR = "ERROR"

    @property
    def is_terminal(self) -> bool:
        return self in {State.ACCEPT, State.HUMAN_REVIEW, State.ERROR}


#: Human-readable reason attached to each terminal state, for the certificate.
TERMINAL_MEANING = {
    State.ACCEPT: "every invariant in the spec passed and the acceptance policy was met",
    State.HUMAN_REVIEW: "the failure was not resolved within budget; the failing rows are listed",
    State.ERROR: "the document could not be processed at all",
}


@dataclass(frozen=True)
class Transition:
    """One row of the table. ``guard`` is a deterministic predicate over the context."""

    source: State
    target: State
    guard: str                      # name in the guard registry; "" means unconditional
    event: str = ""                 # label for the diagram and the log
    description: str = ""

    def label(self) -> str:
        return self.event or self.guard or "always"


class GuardRegistry:
    """Named deterministic predicates. Keeping them named is what makes the log readable:
    the trace says ``row_invariants_ok -> False``, not ``branch 3 taken``."""

    def __init__(self) -> None:
        self._guards: dict[str, Callable[[Any], bool]] = {}
        self._docs: dict[str, str] = {}

    def register(self, name: str, doc: str = "") -> Callable:
        def deco(fn: Callable[[Any], bool]) -> Callable[[Any], bool]:
            if name in self._guards:
                raise ValueError(f"guard {name!r} already registered")
            self._guards[name] = fn
            self._docs[name] = doc or (fn.__doc__ or "").strip().split("\n")[0]
            return fn
        return deco

    def add(self, name: str, fn: Callable[[Any], bool], doc: str = "") -> None:
        self._guards[name] = fn
        self._docs[name] = doc

    def evaluate(self, name: str, ctx: Any) -> bool:
        if not name:
            return True
        try:
            return bool(self._guards[name](ctx))
        except KeyError:
            raise KeyError(f"guard {name!r} is not registered; known: {sorted(self._guards)}") from None

    def doc(self, name: str) -> str:
        return self._docs.get(name, "")

    def names(self) -> list[str]:
        return sorted(self._guards)


@dataclass
class Machine:
    """A state machine as data: states, an initial state and an ordered table."""

    name: str
    initial: State
    transitions: tuple[Transition, ...]
    guards: GuardRegistry = dc_field(default_factory=GuardRegistry)
    max_steps: int = 200

    def outgoing(self, state: State) -> list[Transition]:
        """Transitions out of ``state``, in declaration order. Order is the priority."""
        return [t for t in self.transitions if t.source == state]

    def validate(self) -> None:
        """Every state reachable, every guard registered, every non-terminal state has
        an unconditional fallback so no document can get stuck."""
        for t in self.transitions:
            if t.guard and t.guard not in self.guards.names():
                raise ValueError(f"transition {t.source}->{t.target} uses unregistered guard {t.guard!r}")
        for state in State:
            if state.is_terminal:
                continue
            outs = self.outgoing(state)
            if not outs:
                raise ValueError(f"non-terminal state {state} has no outgoing transition")
            if outs[-1].guard:
                raise ValueError(
                    f"state {state} has no unconditional fallback: the last transition "
                    f"is guarded by {outs[-1].guard!r}, so a document could get stuck")
        reachable = {self.initial}
        frontier = [self.initial]
        while frontier:
            s = frontier.pop()
            for t in self.outgoing(s):
                if t.target not in reachable:
                    reachable.add(t.target)
                    frontier.append(t.target)
        unreachable = set(State) - reachable
        if unreachable:
            raise ValueError(f"unreachable states: {sorted(map(str, unreachable))}")

    def next_transition(self, state: State, ctx: Any) -> tuple[Transition, list[tuple[str, bool]]]:
        """First transition whose guard holds, plus every guard asked and its answer.

        The second element is the audit trail. It is what lets a reader of the log see
        that the machine considered repairing and declined because the budget was spent,
        rather than merely that it escalated.
        """
        asked: list[tuple[str, bool]] = []
        for t in self.outgoing(state):
            ok = self.guards.evaluate(t.guard, ctx)
            if t.guard:
                asked.append((t.guard, ok))
            if ok:
                return t, asked
        raise RuntimeError(f"no transition fired from {state}; validate() should have prevented this")


# --------------------------------------------------------------------------------------
# The table. Order inside each source state is the priority order.
# --------------------------------------------------------------------------------------

TRANSITIONS: tuple[Transition, ...] = (
    Transition(State.INGEST, State.ERROR, "ingest_failed", "no readable page",
               "the file could not be opened or has no pages"),
    Transition(State.INGEST, State.CLASSIFY, "", "ingested"),

    Transition(State.CLASSIFY, State.EXTRACT, "", "classified",
               "digital or scanned, document type, template id"),

    Transition(State.EXTRACT, State.ESCALATE_TIER, "extract_empty_and_tier_left", "nothing extracted",
               "the tier produced no rows and a more expensive tier is available"),
    Transition(State.EXTRACT, State.HUMAN_REVIEW, "extract_empty", "nothing extracted, no tier left"),
    Transition(State.EXTRACT, State.GROUND, "", "candidate reading produced"),

    Transition(State.GROUND, State.VERIFY, "", "every value located or rejected",
               "ungrounded values are marked, never silently kept"),

    Transition(State.VERIFY, State.ACCEPT, "accepts", "all invariants pass and policy met"),
    Transition(State.VERIFY, State.REPAIR, "repairable", "localized failure, repair budget left"),
    Transition(State.VERIFY, State.ESCALATE_TIER, "tier_left", "failure, a better tier is available"),
    Transition(State.VERIFY, State.HUMAN_REVIEW, "", "budget exhausted"),

    Transition(State.REPAIR, State.GROUND, "repair_proposed", "candidate from the source"),
    Transition(State.REPAIR, State.ESCALATE_TIER, "tier_left", "repair found nothing, tier available"),
    Transition(State.REPAIR, State.HUMAN_REVIEW, "", "repair found nothing, no tier left"),

    Transition(State.ESCALATE_TIER, State.EXTRACT, "tier_advanced", "next tier, failed region only"),
    Transition(State.ESCALATE_TIER, State.HUMAN_REVIEW, "", "no tier left within budget"),
)


def build_machine(guards: GuardRegistry) -> Machine:
    m = Machine(name="probity.verified_extraction", initial=State.INGEST,
                transitions=TRANSITIONS, guards=guards)
    m.validate()
    return m
