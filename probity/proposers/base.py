"""What a proposer is, and what it is not allowed to be.

A proposer reads pixels or text and *proposes* a reading. It never decides whether its
reading is correct: that verdict belongs to the deterministic verifiers, and the
interface deliberately gives a proposer no way to express one. There is no
``confidence`` return that the machine routes on (P4), no ``accept`` flag, and no access
to the invariant engine. A proposer may report a confidence for the log, and the log is
where it stays.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field as dc_field
from typing import Any

from ..grounding import DocumentIndex
from ..invariants import Location
from ..records import Statement


@dataclass
class Document:
    """The input: a path, its pages as images when needed, and its page count."""

    doc_id: str
    pdf_path: str | None = None
    page_images: dict[int, str] = dc_field(default_factory=dict)   # page -> png path
    page_count: int = 1
    page_sizes: dict[int, tuple[float, float]] = dc_field(default_factory=dict)
    is_digital: bool | None = None            # set by CLASSIFY
    sha256: str = ""
    meta: dict[str, Any] = dc_field(default_factory=dict)


@dataclass
class Proposal:
    """A candidate reading plus the searchable text that can confirm it.

    ``index`` is what makes grounding possible: the proposer must hand back the text it
    read *with coordinates*, so the grounding engine can check the statement against the
    same evidence rather than trusting the proposer's summary of it.
    """

    statement: Statement
    index: DocumentIndex
    tier: str
    parse_errors: dict[str, int] = dc_field(default_factory=dict)
    notes: list[str] = dc_field(default_factory=list)
    model_confidence: float | None = None     # logged only, never a gate
    #: Every paid call this proposal cost. The pipeline reads cost from here, so a
    #: proposer that keeps its calls to itself reports a run as free when it was not.
    model_calls: list = dc_field(default_factory=list)


class Proposer(abc.ABC):
    """One tier of the ladder."""

    tier: str = "unset"
    cost_class: int = 0        # 0 free, higher is dearer; used only for the ladder order
    #: Does running this tier spend money? A self-hosted OCR model costs GPU time but
    #: not dollars, so it must not be gated by a spend cap: a run configured with no
    #: budget should still be able to read a scan locally. Declared per proposer rather
    #: than inferred from cost_class, and defaulting to True so that a new paid tier
    #: cannot slip past the cap by forgetting to set it.
    bills_usd: bool = True
    #: Can this tier re-read a single region during repair?
    supports_regions: bool = False

    @abc.abstractmethod
    def propose(self, doc: Document, spec, *, region: Location | None = None,
                previous: Statement | None = None) -> Proposal:
        """Read the document, or just ``region`` of it when escalating a local failure.

        When ``region`` is given, the proposer should read only that area and the
        returned statement may contain only the affected rows: the caller splices them
        into the previous reading. Reading the whole document again on every escalation
        is both expensive and a way to turn one bad row into a different set of bad rows.
        """

    def available(self) -> tuple[bool, str]:
        """Whether this tier can run at all right now (model present, key set, ...)."""
        return True, ""
