"""A statement supplied as an image is read exactly like one supplied as a PDF."""

from __future__ import annotations

from dataclasses import replace

import pytest

from probity import Document, DocumentSpec, Pipeline, default_proposers
from probity.images import images_to_pdf, is_image

from test_second_opinion import GOOD, SPEC, FakeReader


def _image(tmp_path, name, size=(200, 280), mode="L"):
    from PIL import Image

    path = tmp_path / name
    Image.new(mode, size, 255 if mode == "L" else (255, 255, 255)).save(path)
    return path


@pytest.mark.parametrize("name", ["scan.png", "photo.jpg", "scan.tiff"])
def test_an_image_file_goes_through_the_machine(tmp_path, name):
    path = _image(tmp_path, name)
    spec = replace(DocumentSpec.load(str(SPEC)), tier_order=("llm_small",))
    reader = FakeReader("reader-a", GOOD, "1,000.00", "1,150.00")
    doc = Document(doc_id="t", pdf_path=str(path))
    result = Pipeline(spec, default_proposers(llm_small=reader)).run(doc)
    assert result.accepted and result.conclusion == "CONFIRMED"
    assert doc.meta["source_image"] == str(path)
    assert doc.page_count == 1


def test_several_images_become_the_pages_of_one_document(tmp_path):
    import pypdfium2 as pdfium

    pages = [_image(tmp_path, f"p{i}.png") for i in range(3)]
    pdf = images_to_pdf(pages, tmp_path / "out.pdf")
    assert len(pdfium.PdfDocument(pdf)) == 3


def test_a_transparent_png_is_flattened_onto_white(tmp_path):
    import pypdfium2 as pdfium
    from PIL import Image

    path = tmp_path / "t.png"
    Image.new("RGBA", (50, 50), (0, 0, 0, 0)).save(path)
    pdf = pdfium.PdfDocument(images_to_pdf([path], tmp_path / "t.pdf"))
    assert pdf[0].render(scale=1).to_numpy().min() > 240


def test_a_pdf_is_not_mistaken_for_an_image(tmp_path):
    pdf = images_to_pdf([_image(tmp_path, "a.png")], tmp_path / "a.pdf")
    assert not is_image(pdf)
    # Judged by content: an image saved under the wrong name is still an image.
    wrong = tmp_path / "statement.pdf.bak"
    wrong.write_bytes(_image(tmp_path, "b.png").read_bytes())
    assert is_image(wrong)
