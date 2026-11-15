"""Build a set of scanned statements from the protocol's split: clean and altered, in tiers.

    python -m benchmark.build_test_set --sources <agami pdf/json dir> \\
        --split sealed_test --out data/sealed

For each source statement in the chosen split, in a seeded order:

1. the statement is corrected so that it ties (``agami_patch.repair``);
2. it is assigned a group (clean, or one kind of alteration) and a scan tier;
3. the alteration, if any, is planted and verified (``alterations.alter``);
4. the pages are flattened to images at the assigned tier (``rasterise``).

Assignment. The groups are a fixed list of slots (so many clean, so many of each kind),
shuffled once with the seed. Statements take slots in order. A statement that cannot
take the kind at the head of the list (a row cannot be whited out on it, or adjusted
balances would go negative) takes the next kind that it can, and the skipped slot stays
at the head for the next statement. Tiers are dealt round-robin over a second seeded
shuffle, so they are independent of the group.

Nothing here looks at any model's output: the assignment depends only on the seed and
on whether the PDF surgery can be done.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

from .external import agami_patch as ap
from .external import alterations as al
from .external.agami import load_dir
from .external.rasterise import TIERS, assert_no_text_layer, rasterise

#: Slots for the sealed test of 120 statements (protocol section 4.1).
SEALED_SLOTS = {"clean": 40, "amount": 16, "balance": 12, "row_removed": 12,
                "direction": 12, "amount_adjusted": 12, "row_adjusted": 8, "text": 8}


def _slots(counts: dict[str, int], rng: random.Random) -> list[str]:
    out = [k for k, n in counts.items() for _ in range(n)]
    rng.shuffle(out)
    return out


def scaled_slots(n: int) -> dict[str, int]:
    """The sealed proportions, scaled to ``n`` statements (for development sets)."""
    total = sum(SEALED_SLOTS.values())
    counts = {k: max(1, round(v * n / total)) for k, v in SEALED_SLOTS.items()}
    while sum(counts.values()) > n:
        counts[max(counts, key=counts.get)] -= 1
    while sum(counts.values()) < n:
        counts["clean"] += 1
    return counts


def build(sources: str, split: str, out_dir: str, *, seed: int = 20261115,
          limit: int | None = None, slots: dict[str, int] | None = None) -> dict[str, Any]:
    protocol = json.loads((Path(__file__).parent / "protocol" / "split.json")
                          .read_text(encoding="utf-8"))
    wanted = list(protocol[split])
    rng = random.Random(f"{seed}:{split}")
    rng.shuffle(wanted)
    if limit:
        wanted = wanted[:limit]
    counts = slots or (SEALED_SLOTS if split == "sealed_test" and not limit
                       else scaled_slots(len(wanted)))
    queue = _slots(counts, rng)
    tiers = [TIERS[i % len(TIERS)] for i in range(len(wanted))]
    rng.shuffle(tiers)

    docs = {d.doc_id: d for d in load_dir(sources) if d.render == "digital"}
    out = Path(out_dir)
    (out / "digital").mkdir(parents=True, exist_ok=True)
    records, skipped = [], []
    for n, (source_id, tier) in enumerate(zip(wanted, tiers)):
        doc = docs[source_id]
        short = source_id.replace("agami-Digital_", "")
        clean_pdf = str(out / "digital" / f"{short}-clean.pdf")
        rep = ap.repair(doc.pdf, doc.truth, clean_pdf)
        if rep is None or ap.read_back(clean_pdf, rep.truth):
            skipped.append({"source": source_id, "why": "could not be corrected to tie"})
            continue

        truth, digital, group = None, None, None
        for k, kind in enumerate(queue):
            if kind == "clean":
                truth, digital, group = dict(rep.truth), clean_pdf, "clean"
                truth["alteration"] = None
            else:
                target = str(out / "digital" / f"{short}-{kind}.pdf")
                try:
                    truth = al.alter(kind, clean_pdf, rep.truth, target,
                                     random.Random(f"{seed}:{source_id}:{kind}"))
                except al.CannotBuild:
                    continue
                digital, group = target, kind
            queue.pop(k)
            break
        if truth is None:
            skipped.append({"source": source_id, "why": "no remaining group could be built"})
            continue

        doc_id = f"{short}-{group}-{tier}"
        scan = str(out / f"{doc_id}.pdf")
        info = rasterise(digital, scan, doc_id=f"{seed}:{source_id}", tier=tier)
        assert_no_text_layer(scan)
        truth["doc_id"] = doc_id
        truth_path = out / f"{doc_id}.truth.json"
        truth_path.write_text(json.dumps(truth, indent=1, ensure_ascii=False),
                              encoding="utf-8")
        alteration = truth.get("alteration") or {}
        records.append({
            "doc_id": doc_id, "source": source_id, "layout": doc.layout,
            "group": group, "tier": tier,
            "detectable_by_arithmetic": alteration.get("detectable_by_arithmetic"),
            "expected_rows": alteration.get("expected_rows", []),
            "alteration": alteration.get("detail"),
            "document": scan, "truth": str(truth_path),
            "spec": f"examples/specs/agami_{doc.layout}.yaml",
            "rows": len(truth["ledger"]["rows"]), "pages": info["pages"],
            "sha256": hashlib.sha256(Path(scan).read_bytes()).hexdigest(),
        })
        print(f"[{n + 1}/{len(wanted)}] {doc_id}", flush=True)

    manifest = {"split": split, "seed": seed, "documents": records, "skipped": skipped,
                "unfilled_slots": queue,
                "counts": {g: sum(r["group"] == g for r in records) for g in counts},
                "tiers": {t: sum(r["tier"] == t for r in records) for t in TIERS}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False),
                                       encoding="utf-8")
    return manifest


def main() -> None:
    ap_ = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap_.add_argument("--sources", required=True, help="directory of AgamiAI pdf/json pairs")
    ap_.add_argument("--split", required=True,
                     choices=["development_unseen", "sealed_test"])
    ap_.add_argument("--out", required=True)
    ap_.add_argument("--limit", type=int, default=None)
    ap_.add_argument("--seed", type=int, default=20261115)
    args = ap_.parse_args()
    m = build(args.sources, args.split, args.out, seed=args.seed, limit=args.limit)
    print(json.dumps({"counts": m["counts"], "tiers": m["tiers"],
                      "skipped": len(m["skipped"]), "unfilled": m["unfilled_slots"]}))


if __name__ == "__main__":
    main()
