from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from scripts import assets


SVG_NS = {"svg": "http://www.w3.org/2000/svg"}
ROOT = Path(__file__).resolve().parents[1]


def _root(svg: str) -> ET.Element:
    return ET.fromstring(svg)


def test_generated_comment_is_independent_of_wall_clock(tmp_path, monkeypatch):
    first = tmp_path / "first.svg"
    second = tmp_path / "second.svg"
    real_datetime = assets._dt.datetime

    class Morning:
        @classmethod
        def now(cls, _timezone):
            return real_datetime(2026, 1, 1, tzinfo=assets._dt.timezone.utc)

    class Evening:
        @classmethod
        def now(cls, _timezone):
            return real_datetime(2027, 12, 31, tzinfo=assets._dt.timezone.utc)

    monkeypatch.setattr(assets._dt, "datetime", Morning)
    assets._write(str(first), "<svg/>", "fixture.csv")
    monkeypatch.setattr(assets._dt, "datetime", Evening)
    assets._write(str(second), "<svg/>", "fixture.csv")

    assert first.read_bytes() == second.read_bytes()


def test_every_svg_builder_emits_title_and_description():
    svgs = [
        assets._svg(assets.logo_break(assets.P["red"]), description="Interrupted bar logo"),
        assets.icon_svg("break", assets.P),
        assets.lockup_svg("break", assets.P),
        *[assets.mark_svg(name) for name in assets.MARKS],
    ]

    for svg in svgs:
        root = _root(svg)
        assert len(root.findall("svg:title", SVG_NS)) == 1
        assert len(root.findall("svg:desc", SVG_NS)) == 1


def test_every_committed_public_svg_has_title_and_description():
    for path in (ROOT / "frontend" / "public").rglob("*.svg"):
        root = ET.parse(path).getroot()
        assert len(root.findall("svg:title", SVG_NS)) == 1, path
        assert len(root.findall("svg:desc", SVG_NS)) == 1, path


def test_png_writer_emits_the_canonical_cross_platform_encoding(tmp_path):
    writer = getattr(assets, "_write_deterministic_png", None)
    assert writer is not None, "assets need a canonical PNG writer"

    image = Image.new("RGB", (2, 2))
    pixels = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)]
    image.putdata(pixels)
    output = tmp_path / "fixture.png"

    writer(image, output)

    assert hashlib.sha256(output.read_bytes()).hexdigest() == (
        "728cbedc0432e9c62e1d3f8b0b2dc65743a953e255b7e482d80f2e239e48f450"
    )
    with Image.open(output) as decoded:
        assert list(decoded.convert("RGB").get_flattened_data()) == pixels
