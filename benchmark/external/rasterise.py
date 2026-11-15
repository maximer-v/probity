"""Turn a built digital statement into an image-only one, the way a scanner would.

Why this exists. The documents a reconciliation tool is actually pointed at are scans
and photographs, not born-digital PDFs with a text layer. The publisher ships scanned
versions of these same statements, but only of the originals -- there is no scanned
twin of a document whose amounts we corrected or altered. So the built corpus is
rasterised here instead, which also buys exact control: the surgery happens in the
content stream, where a cell can be rewritten and checked against the printed glyphs,
and only then is the page flattened to pixels.

The one property that matters for the benchmark is that **the clean and the altered
documents go through exactly the same pipeline**: the same effects, the same
parameters, the same code path. The random state for each document is seeded from a
hash of its output name. That name ends in the group (``-scan-repaired`` or
``-scan-tampered``), so the seed is not independent of the group. It carries no usable
signal: every document is a different statement with
its own noise field, there is no clean twin of an altered document to compare against,
and recovering the group from the noise would mean inverting SHA-256. It is recorded
here because "the rendering cannot depend on the group" would be a stronger claim than
this code supports.

What is simulated, and what is not:

  * grayscale, because these scans are
  * a smooth lighting gradient, the uneven illumination of a flatbed or a phone
  * a slight defocus blur
  * sensor noise
  * JPEG compression, which is what scanners emit

Three tiers are available. T1 is the above and nothing more: a flatbed scan, square to
the page. T2 adds a rotation of up to 2 degrees and a shadow band. T3 adds a perspective
distortion, stronger blur, more noise and harder compression, as from a phone held over
the page. None of them reproduces creases, stamps, handwriting or a curved page.

Resolution is 300 dpi, matching the publisher's own scans (2481 x 3508 for A4).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

#: A4 at 300 dpi, which is what the publisher's own scanned split uses.
SCAN_DPI = 300
#: Quality of the JPEG a scanner would hand you. Low enough to be real, high enough
#: that the digits survive -- the point is a realistic document, not an unreadable one.
JPEG_QUALITY = 85


def _rng_for(doc_id: str) -> np.random.Generator:
    """Deterministic per document: a hash of the name it is given.

    Not a global counter, so documents can be rebuilt one at a time and in any order.
    See the module docstring for what the name contains.
    """
    digest = hashlib.sha256(doc_id.encode("utf-8")).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "big"))


def _lighting(shape: tuple[int, int], rng: np.random.Generator) -> np.ndarray:
    """A smooth multiplicative illumination field, bilinear-upsampled from a coarse grid.

    Built small and stretched rather than generated per pixel, so it is smooth by
    construction -- real uneven lighting has no high-frequency component.
    """
    h, w = shape
    coarse = rng.uniform(0.86, 1.04, size=(4, 4))
    ys = np.linspace(0, 3, h)
    xs = np.linspace(0, 3, w)
    y0 = np.clip(np.floor(ys).astype(int), 0, 2)
    x0 = np.clip(np.floor(xs).astype(int), 0, 2)
    fy = (ys - y0)[:, None]
    fx = (xs - x0)[None, :]
    c = coarse
    top = c[y0][:, x0] * (1 - fx) + c[y0][:, x0 + 1] * fx
    bot = c[y0 + 1][:, x0] * (1 - fx) + c[y0 + 1][:, x0 + 1] * fx
    return top * (1 - fy) + bot * fy


def _blur3(a: np.ndarray, passes: int) -> np.ndarray:
    """A separable 3-tap blur, applied `passes` times. Approximates a small defocus."""
    out = a
    for _ in range(passes):
        p = np.pad(out, 1, mode="edge")
        out = (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:] + 4 * out) / 8.0
    return out


def degrade(page_rgb: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """One rendered page, as a scanner would have delivered it."""
    g = page_rgb[..., :3].mean(axis=2).astype(np.float32)
    g = _blur3(g, passes=1)
    g = g * _lighting(g.shape, rng)
    g = g + rng.normal(0.0, 2.2, size=g.shape).astype(np.float32)
    return np.clip(g, 0, 255).astype(np.uint8)


#: Scan tiers. T1 is a flatbed scan; T2 a page fed slightly crooked under uneven light;
#: T3 a photograph taken with a phone, seen at an angle and less sharp.
TIERS = ("T1", "T2", "T3")


def _shadow(shape: tuple[int, int], rng: np.random.Generator) -> np.ndarray:
    """A soft dark band across the page, as cast by a hand or the scanner lid."""
    h, w = shape
    centre = rng.uniform(0.15, 0.85) * h
    width = rng.uniform(0.08, 0.16) * h
    depth = rng.uniform(0.10, 0.20)
    ys = np.arange(h, dtype=np.float32)[:, None]
    return 1.0 - depth * np.exp(-((ys - centre) ** 2) / (2 * width ** 2)) * np.ones((1, w))


def _perspective(img, rng: np.random.Generator):
    """View the page at a slight angle: each corner moves by up to about 2% of the page."""
    from PIL import Image

    w, h = img.size
    jitter = lambda scale: float(rng.uniform(0.004, 0.022)) * scale  # noqa: E731
    dst = [(jitter(w), jitter(h)), (w - jitter(w), jitter(h)),
           (w - jitter(w), h - jitter(h)), (jitter(w), h - jitter(h))]
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    # Coefficients mapping output pixels back to input pixels (what PIL expects).
    rows = []
    for (x, y), (u, v) in zip(dst, src):
        rows.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        rows.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    target = np.array([c for pair in src for c in pair], dtype=np.float64)
    coeffs = np.linalg.solve(np.array(rows, dtype=np.float64), target)
    return img.transform((w, h), Image.PERSPECTIVE, tuple(coeffs), Image.BICUBIC,
                         fillcolor=235)


def degrade_tier(page_rgb: np.ndarray, rng: np.random.Generator, tier: str):
    """One rendered page as tier ``tier`` would have delivered it. Returns a PIL image."""
    from PIL import Image

    if tier == "T1":
        return Image.fromarray(degrade(page_rgb, rng), mode="L")
    g = page_rgb[..., :3].mean(axis=2).astype(np.float32)
    if tier == "T2":
        g = _blur3(g, passes=1)
        g = g * _lighting(g.shape, rng) * _shadow(g.shape, rng)
        g = g + rng.normal(0.0, 2.6, size=g.shape).astype(np.float32)
        img = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8), mode="L")
        angle = float(rng.uniform(0.5, 2.0)) * (1 if rng.random() < 0.5 else -1)
        return img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=240)
    if tier == "T3":
        g = _blur3(g, passes=3)
        g = g * _lighting(g.shape, rng) * _shadow(g.shape, rng)
        g = g + rng.normal(0.0, 4.0, size=g.shape).astype(np.float32)
        img = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8), mode="L")
        angle = float(rng.uniform(0.3, 1.2)) * (1 if rng.random() < 0.5 else -1)
        img = img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=235)
        return _perspective(img, rng)
    raise ValueError(f"unknown scan tier {tier!r}")


#: JPEG quality by tier. A phone's upload is compressed harder than a scanner's output.
TIER_QUALITY = {"T1": JPEG_QUALITY, "T2": 80, "T3": 62}


def rasterise(pdf_path: str, out_path: str, doc_id: str,
              dpi: int = SCAN_DPI, tier: str = "T1") -> dict[str, Any]:
    """Flatten a PDF to an image-only PDF. Returns what was done, for the manifest."""
    import pypdfium2 as pdfium

    rng = _rng_for(doc_id)
    pdf = pdfium.PdfDocument(pdf_path)
    pages = []
    for i in range(len(pdf)):
        page = pdf[i]
        long_edge = max(page.get_width(), page.get_height())
        scale = (dpi / 72.0 * 841.89) / long_edge if long_edge else dpi / 72.0
        arr = page.render(scale=scale).to_numpy()
        pages.append(degrade_tier(arr, rng, tier))

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    quality = TIER_QUALITY[tier]
    pages[0].save(out_path, save_all=True, append_images=pages[1:],
                  resolution=float(dpi), quality=quality)
    return {"pages": len(pages), "dpi": dpi, "size": pages[0].size, "tier": tier,
            "jpeg_quality": quality,
            "effects": {"T1": ["grayscale", "defocus", "lighting", "noise", "jpeg"],
                        "T2": ["grayscale", "defocus", "lighting", "shadow", "noise",
                               "rotation", "jpeg"],
                        "T3": ["grayscale", "strong defocus", "lighting", "shadow",
                               "noise", "rotation", "perspective", "jpeg"]}[tier],
            "skew": tier != "T1"}


def assert_no_text_layer(pdf_path: str) -> int:
    """A scanned document that still carries its text is not a scanned document.

    Guards the whole point of the corpus: if PIL or pdfium ever started preserving the
    text, the tier ladder would quietly fall back to the text layer and the benchmark
    would be measuring the wrong thing while still looking like it worked.
    """
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(pdf_path)
    total = 0
    for i in range(len(doc)):
        total += len((doc[i].get_textpage().get_text_range() or "").strip())
    if total:
        raise AssertionError(f"{pdf_path} still carries {total} text characters")
    return total


def build_scanned(built_manifest: str, out_dir: str,
                  limit: int | None = None) -> dict[str, Any]:
    """Rasterise an already-built (repaired / tampered) corpus."""
    man = json.loads(Path(built_manifest).read_text(encoding="utf-8"))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    records = []
    docs = man["documents"][:limit] if limit else man["documents"]
    for d in docs:
        stem = d["doc_id"].replace("-repaired", "").replace("-tampered", "")
        stem = f"{stem}-scan-{d['kind']}"
        pdf_out = str(out / f"{stem}.pdf")
        info = rasterise(d["document"], pdf_out, doc_id=stem)
        assert_no_text_layer(pdf_out)

        truth = json.loads(Path(d["truth"]).read_text(encoding="utf-8"))
        truth["doc_id"] = stem
        truth["render"] = "scanned"
        # Coordinates came from the digital original and do not survive flattening.
        truth["boxes"] = {}
        truth["has_box_truth"] = False
        tp = out / f"{stem}.truth.json"
        tp.write_text(json.dumps(truth, indent=1, ensure_ascii=False), encoding="utf-8")

        rec = dict(d)
        rec.update({"doc_id": stem, "document": pdf_out, "truth": str(tp),
                    # Of the image-only file that is actually read, not of the digital
                    # source it was flattened from.
                    "sha256": hashlib.sha256(Path(pdf_out).read_bytes()).hexdigest(),
                    "sha256_digital_source": d.get("sha256"),
                    "render": "scanned", "is_digital": False,
                    "digital_source": d["document"], "scan": info})
        records.append(rec)
        print(f"  {stem:44} {info['pages']} pages  {info['size']}  "
              f"{d['kind']:9} no text layer", flush=True)

    manifest = {"split": "external_agami_scanned",
                "source": man.get("source"),
                "built_by": "benchmark/external/rasterise.py from "
                            + str(built_manifest),
                "documents": records,
                "counts": {"repaired": sum(1 for r in records if r["kind"] == "repaired"),
                           "tampered": sum(1 for r in records if r["kind"] == "tampered")}}
    mp = out / "manifest.json"
    mp.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    manifest["manifest_path"] = str(mp)
    return manifest
