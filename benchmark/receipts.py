"""Real scanned receipts (CORD) as a second document type, clean and altered.

CORD is a public corpus of photographed Indonesian receipts with the items, subtotal,
tax, total, cash and change transcribed, and the position of every word on the image.

    python -m benchmark.receipts build --splits validation --out data/receipts_dev
    python -m benchmark.receipts build --splits test train --out data/receipts_sealed --limit 100

A receipt is used only if its published transcription satisfies the rules of the
receipt spec, has at least two items and a total: a receipt whose own figures do not
add up cannot serve as a clean document.

Every receipt used is retouched in exactly one place: one printed amount (a line amount
or the total) is painted over and redrawn. In the altered half the digits are changed so
that a rule no longer holds; in the clean half the same digits are redrawn. The
retouching is visible to a careful eye, and because both groups carry it, it cannot be
what tells them apart.
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import random
from pathlib import Path
from typing import Any

from probity.forms import FormSpec, build_reading, check, parse_money

REPO = "naver-clova-ix/cord-v2"
SPEC_PATH = Path(__file__).resolve().parents[1] / "examples" / "specs" / "receipt_cord.yaml"


def load_split(split: str) -> list[dict[str, Any]]:
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download, list_repo_files

    rows: list[dict[str, Any]] = []
    for name in sorted(f for f in list_repo_files(REPO, repo_type="dataset")
                       if f.startswith(f"data/{split}-")):
        rows += pq.read_table(hf_hub_download(REPO, name, repo_type="dataset")).to_pylist()
    return rows


def _first(value: Any) -> Any:
    return value[0] if isinstance(value, list) and value else value


def to_form(gt: dict[str, Any]) -> dict[str, Any] | None:
    """CORD's transcription in the shape of the receipt spec. None if it does not fit."""
    parse = gt.get("gt_parse") or {}
    menu = parse.get("menu")
    menu = menu if isinstance(menu, list) else [menu] if isinstance(menu, dict) else []
    sub = _first(parse.get("sub_total")) or {}
    total = _first(parse.get("total")) or {}
    if not isinstance(sub, dict) or not isinstance(total, dict):
        return None
    items = []
    for m in menu:
        if not isinstance(m, dict) or "sub" in m or "discountprice" in m:
            return None                       # nested or discounted lines: out of scope
        if isinstance(m.get("price"), list) or isinstance(m.get("nm"), list):
            return None
        items.append({"name": m.get("nm"), "quantity": m.get("cnt"),
                      "unit_price": m.get("unitprice"), "price": m.get("price")})
    if any(isinstance(v, list) for v in list(sub.values()) + list(total.values())):
        return None
    return {"subtotal": sub.get("subtotal_price"), "tax": sub.get("tax_price"),
            "service": sub.get("service_price"), "discount": sub.get("discount_price"),
            "total": total.get("total_price"), "cash": total.get("cashprice"),
            "change": total.get("changeprice"), "items": items}


def usable(form: dict[str, Any] | None, spec: FormSpec) -> bool:
    if form is None or len(form["items"]) < 2 or form.get("total") is None:
        return False
    reading = build_reading(form, spec)
    if reading.fields.get("total") is None:
        return False
    if any(r.get("price") is None for r in reading.tables["items"]):
        return False
    if form.get("discount") is not None or "etc" in form:
        return False
    return not check(reading, spec)


def _price_words(gt: dict[str, Any]) -> list[dict[str, Any]]:
    """Single-word line amounts and totals, with their box, in reading order."""
    out = []
    item = -1
    seen_groups: list[int] = []
    for line in gt.get("valid_line") or []:
        cat, words = line.get("category"), line.get("words") or []
        gid = line.get("group_id")
        if str(cat).startswith("menu.") and gid not in seen_groups:
            seen_groups.append(gid)
        if cat not in ("menu.price", "total.total_price") or len(words) != 1:
            continue
        w = words[0]
        if w.get("is_key"):
            continue
        q = w["quad"]
        box = (min(q["x1"], q["x4"]), min(q["y1"], q["y2"]),
               max(q["x2"], q["x3"]), max(q["y3"], q["y4"]))
        out.append({"category": cat, "text": w["text"], "box": box,
                    "item": seen_groups.index(gid) if cat == "menu.price" else None})
    return out


def _alter_digits(text: str, rng: random.Random) -> str | None:
    """Change one digit that is not the last three (so the amount moves materially)."""
    positions = [i for i, ch in enumerate(text) if ch.isdigit()]
    if len(positions) < 4:
        return None
    candidates = positions[:-3]
    i = rng.choice(candidates)
    old = text[i]
    choices = [d for d in "123456789" if d != old] if i == positions[0] else \
        [d for d in "0123456789" if d != old]
    return text[:i] + rng.choice(choices) + text[i + 1:]


def _paint(image, box: tuple[int, int, int, int], new_text: str):
    """Paint over one word and draw ``new_text`` in its place."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    img = image.convert("RGB")
    x0, y0, x1, y1 = [int(v) for v in box]
    pad = 2
    x0, y0, x1, y1 = max(0, x0 - pad), max(0, y0 - pad), min(img.width, x1 + pad), min(img.height, y1 + pad)
    arr = np.asarray(img).astype(np.int32)
    patch = arr[y0:y1, x0:x1].reshape(-1, 3)
    ring = np.concatenate([arr[max(0, y0 - 4):y0, x0:x1].reshape(-1, 3),
                           arr[y1:y1 + 4, x0:x1].reshape(-1, 3)]) if y0 > 4 else patch
    background = tuple(int(v) for v in np.median(ring if len(ring) else patch, axis=0))
    luminance = patch.sum(axis=1)
    ink = tuple(int(v) for v in np.median(patch[luminance <= np.percentile(luminance, 12)], axis=0))

    draw = ImageDraw.Draw(img)
    draw.rectangle((x0, y0, x1, y1), fill=background)
    height, width = y1 - y0, x1 - x0
    font = None
    for name in ("DejaVuSansMono.ttf", "DejaVuSans.ttf", "LiberationMono-Regular.ttf"):
        try:
            size = max(8, int(height * 0.95))
            font = ImageFont.truetype(name, size)
            while size > 8 and draw.textlength(new_text, font=font) > width:
                size -= 1
                font = ImageFont.truetype(name, size)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()
    tw = draw.textlength(new_text, font=font)
    bbox = draw.textbbox((0, 0), new_text, font=font)
    draw.text((x1 - tw - pad, y0 + (height - (bbox[3] - bbox[1])) / 2 - bbox[1]),
              new_text, fill=ink, font=font)
    region = img.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(0.6))
    img.paste(region, (x0, y0))
    return img


def _candidates(split: str, spec: FormSpec) -> tuple[list[tuple], int]:
    rows = load_split(split)
    out = []
    for n, row in enumerate(rows):
        gt = json.loads(row["ground_truth"])
        form = to_form(gt)
        if usable(form, spec):
            out.append((split, n, row, gt, form))
    return out, len(rows)


def _retouch(image, gt, form, spec, rng, *, change: bool):
    """Repaint one printed amount. Returns (image, truth form, detail) or None.

    With ``change`` the digits are altered so that a rule fails. Without it the same
    word is painted over and redrawn with the SAME digits. Every receipt in the set is
    retouched in one place, so a retouched word cannot tell the two groups apart.
    """
    words = _price_words(gt)
    rng.shuffle(words)
    for w in words:
        new_text = _alter_digits(w["text"], rng) if change else w["text"]
        if new_text is None:
            continue
        trial = copy.deepcopy(form)
        if w["category"] == "total.total_price":
            if parse_money(w["text"], spec.amounts) != parse_money(form["total"], spec.amounts):
                continue
            trial["total"], where = new_text, "total"
        else:
            i = w["item"]
            if i is None or i >= len(trial["items"]) or parse_money(
                    w["text"], spec.amounts) != parse_money(trial["items"][i]["price"],
                                                            spec.amounts):
                continue
            trial["items"][i]["price"], where = new_text, f"items[{i}].price"
        failing = check(build_reading(trial, spec), spec)
        if bool(failing) != change:
            continue
        detail = {"where": where, "from": w["text"], "to": new_text,
                  "expected_rules": sorted({f.rule for f in failing})}
        return _paint(image, w["box"], new_text), trial, detail
    return None


def build(splits: list[str], out_dir: str, *, limit: int | None = None,
          seed: int = 20261115) -> dict[str, Any]:
    """Build a balanced set from ``splits``, taken in the order given.

    Every usable receipt of the first split is used, in a seeded order, then usable
    receipts of the next split, until ``limit`` is reached. Groups alternate, and a
    receipt on which the required retouching cannot be done with certainty is skipped
    and replaced by the next candidate, so the two groups stay the same size.
    """
    from PIL import Image

    spec = FormSpec.load(SPEC_PATH)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pool, sizes = [], {}
    for split in splits:
        found, n = _candidates(split, spec)
        random.Random(f"{seed}:receipts:{split}").shuffle(found)
        pool += found
        sizes[split] = {"receipts": n, "usable": len(found)}
    rng = random.Random(f"{seed}:receipts:retouch")
    target = limit or len(pool)
    target -= target % 2
    records, skipped = [], []
    for split, n, row, gt, form in pool:
        if len(records) >= target:
            break
        group = "altered" if sum(r["group"] == "clean" for r in records) > \
            sum(r["group"] == "altered" for r in records) else "clean"
        image = Image.open(io.BytesIO(row["image"]["bytes"])).convert("RGB")
        done = _retouch(image, gt, form, spec, rng, change=(group == "altered"))
        if done is None:
            skipped.append({"split": split, "index": n,
                            "why": f"no amount could be repainted for group {group}"})
            continue
        image, truth, detail = done
        doc_id = f"cord-{split}-{n:04d}-{group}"
        path = out / f"{doc_id}.png"
        image.save(path)
        truth_path = out / f"{doc_id}.truth.json"
        truth_path.write_text(json.dumps(
            {"doc_id": doc_id, "form": truth,
             "alteration": detail if group == "altered" else None,
             "repainted": {"where": detail["where"], "text": detail["to"]}},
            indent=1, ensure_ascii=False), encoding="utf-8")
        records.append({"doc_id": doc_id, "group": group, "source_split": split,
                        "document": str(path), "truth": str(truth_path),
                        "alteration": detail if group == "altered" else None,
                        "items": len(truth["items"])})
    # The two groups must be the same size. If the candidates ran out with one group
    # ahead, the last receipt of the larger group is removed.
    for g, other in (("clean", "altered"), ("altered", "clean")):
        while sum(r["group"] == g for r in records) > sum(r["group"] == other for r in records):
            extra = [r for r in records if r["group"] == g][-1]
            records.remove(extra)
            Path(extra["document"]).unlink(missing_ok=True)
            Path(extra["truth"]).unlink(missing_ok=True)
            skipped.append({"doc_id": extra["doc_id"], "why": "removed to keep the groups equal"})
    manifest = {"source": REPO, "splits": sizes, "seed": seed,
                "requested": target, "built": len(records),
                "documents": records, "skipped": skipped,
                "counts": {g: sum(r["group"] == g for r in records)
                           for g in ("clean", "altered")},
                "by_split": {sp: sum(r["source_split"] == sp for r in records)
                             for sp in splits}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False),
                                       encoding="utf-8")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--splits", required=True, nargs="+",
                   choices=["train", "validation", "test"],
                   help="splits to draw from, in order")
    b.add_argument("--out", required=True)
    b.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    m = build(args.splits, args.out, limit=args.limit)
    print(json.dumps({k: m[k] for k in ("splits", "counts", "by_split", "requested", "built")}),
          "skipped", len(m["skipped"]))
    if m["built"] < m["requested"]:
        raise SystemExit(f"only {m['built']} of the {m['requested']} receipts requested "
                         f"could be built; add a split or lower --limit")


if __name__ == "__main__":
    main()
