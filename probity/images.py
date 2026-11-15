"""Accept a photograph or a scan saved as an image, not only a PDF.

A statement arrives as whatever the customer had to hand: a PDF from online banking, a
flatbed scan, or a phone photo of each page. The machine downstream reads pages, so an
image input is wrapped into an image-only PDF, one page per image (or per frame of a
multi-page TIFF), and everything after INGEST is identical for both.

Nothing is read or recognised here. Three things do happen to the pixels, and are
worth knowing: the EXIF orientation is applied, so a phone photo is not presented
sideways; transparency is flattened onto white; and each page is stored in the wrapper
as a JPEG at quality 95, which is a re-encode and not a byte-for-byte copy. The hash
recorded for the document is that of the file supplied, not of the wrapper. The wrapper
is written to the system temp directory and is not removed afterwards.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Iterable

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".bmp", ".gif"}

#: High enough that wrapping a page does not cost digits. Pages inside a PDF are stored
#: as JPEG; this is the quality of that one re-encode.
WRAP_QUALITY = 95


def is_image(path: str | Path) -> bool:
    """Is this file an image, judged by its content first and its name second?"""
    p = Path(path)
    try:
        head = p.open("rb").read(12)
    except OSError:
        return False
    if head.startswith(b"%PDF"):
        return False
    magic = (head.startswith(b"\x89PNG") or head.startswith(b"\xff\xd8")
             or head[:4] in (b"II*\x00", b"MM\x00*") or head.startswith(b"BM")
             or head[:4] == b"GIF8" or (head[:4] == b"RIFF" and head[8:12] == b"WEBP"))
    return magic or p.suffix.lower() in IMAGE_SUFFIXES


def images_to_pdf(paths: Iterable[str | Path], out_path: str | Path | None = None) -> str:
    """Wrap one or more images into a single image-only PDF, in the order given."""
    from PIL import Image, ImageOps, ImageSequence

    pages = []
    for path in paths:
        with Image.open(path) as im:
            for frame in ImageSequence.Iterator(im):
                page = ImageOps.exif_transpose(frame.copy())
                if page.mode in ("RGBA", "LA", "P"):
                    rgba = page.convert("RGBA")
                    white = Image.new("RGB", rgba.size, (255, 255, 255))
                    white.paste(rgba, mask=rgba.split()[-1])
                    page = white
                elif page.mode not in ("L", "RGB"):
                    page = page.convert("RGB")
                pages.append(page)
    if not pages:
        raise ValueError("no image pages to read")

    if out_path is None:
        out_path = Path(tempfile.mkdtemp(prefix="probity-")) / "document.pdf"
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(out_path, "PDF", save_all=True, append_images=pages[1:],
                  resolution=300.0, quality=WRAP_QUALITY)
    return str(out_path)
