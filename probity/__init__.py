"""probity: verified extraction of financial documents.

Models propose, deterministic code decides. The generation is not deterministic; the
*verdict* is. An OCR model or an LLM may read a bank statement however it likes, and a
state machine then accepts, repairs or escalates that reading using only accounting
invariants and grounding checks. No model is ever asked whether its own output is right.

    from probity import DocumentSpec, Pipeline, Document, default_proposers

    reader = vlm_proposer("google/gemini-3.1-flash-lite")
    second = vlm_proposer("qwen/qwen3.5-flash-02-23", tier="checker", client=reader.client)
    spec = DocumentSpec.load("examples/specs/agami_type2.yaml")
    result = Pipeline(spec, default_proposers(llm_small=reader, checker=second)).run(
        Document("stmt", "scan.pdf"))        # a PDF or an image

    print(result.conclusion)                 # CONFIRMED / DOCUMENT_INCONSISTENT / UNRESOLVED
    print(result.corrections)                # what the first reading got wrong
    print(result.trace.explain())            # every rule asked, and why it answered
"""

from __future__ import annotations

__version__ = "0.2.0"

from .certificate import Certificate
from .dates import DateParseError, parse_date
from .grounding import DocumentIndex, GroundingCode, ground_statement
from .invariants import REGISTRY as INVARIANTS, Location, Scope, run_invariants
from .machine import State, Transition, build_machine
from .money import Locale, Money, get_locale, parse_amount
from .pipeline import Pipeline, Result
from .proposers.base import Document, Proposal, Proposer
from .report import render_report
from .records import BBox, Field, Provenance, Row, Statement, Status
from .spec import DocumentSpec
from .trace import Trace

__all__ = [
    "__version__", "BBox", "Certificate", "DateParseError", "Document", "DocumentIndex",
    "DocumentSpec", "Field", "GroundingCode", "INVARIANTS", "Locale", "Location",
    "Money", "Pipeline", "Proposal", "Proposer", "Provenance", "Result", "Row", "Scope",
    "State", "Statement", "Status", "Trace", "Transition", "build_machine", "get_locale",
    "ground_statement", "parse_amount", "parse_date", "run_invariants",
    "default_proposers", "vlm_proposer", "render_report",
]


def default_proposers(*, llm_small=None, llm_large=None, checker=None) -> dict:
    """The free tier, plus any model tiers the caller supplies.

    Nothing that costs money is enabled by default: a tier that calls a paid API appears
    in the ladder only when it is passed in explicitly, so a run with no configuration
    reads digital PDFs for free and refuses everything else.
    """
    from .proposers.text_layer import TextLayerProposer

    out: dict = {"text_layer": TextLayerProposer()}
    if llm_small is not None:
        out["llm_small"] = llm_small
    if llm_large is not None:
        out["llm_large"] = llm_large
    if checker is not None:
        # Not a rung of the ladder: it never reads a whole document. It is asked only
        # about a page on which a rule failed. See probity/second_opinion.py.
        out["checker"] = checker
    return out


def vlm_proposer(model: str, *, cap_usd: float = 5.0, tier: str = "llm_small",
                 provider: str | None = None, api_key: str | None = None,
                 cache_dir: str = ".probity-cache", client=None):
    """A vision model as a reader, in one call.

        reader = vlm_proposer("google/gemini-3.1-flash-lite")
        second = vlm_proposer("qwen/qwen3.5-flash-02-23", tier="checker",
                              client=reader.client)
        proposers = default_proposers(llm_small=reader, checker=second)

    ``tier="checker"`` makes it the second reader: it never reads a whole document, only
    a page on which a rule has failed. Pass the first reader's ``client`` so both share
    one spend cap and one cache.

    Pages are sent one per request. A long statement asked for in a single reply comes
    back with the right number of rows and the values decaying along it.
    """
    from .openrouter import OpenRouterClient, build_panel
    from .proposers.vlm import VLMProposer

    if client is None:
        client = OpenRouterClient(cap_usd=cap_usd, api_key=api_key, cache_dir=cache_dir,
                                  ledger_path=f"{cache_dir}/spend_ledger.jsonl")
    spec = build_panel([(tier, model, provider)])[0]
    # Some providers refuse a structured-output request unless the prompt says "json".
    # Only the second reader gets the extra line, so the first reader's prompt is the
    # one the benchmark measured.
    suffix = "\nReply with a single JSON object." if tier == "checker" else ""
    return VLMProposer(client=client, model=spec, tier=tier, pages_per_call=1,
                       prompt_suffix=suffix)
