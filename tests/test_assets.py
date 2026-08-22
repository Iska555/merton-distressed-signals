from __future__ import annotations

import csv
import xml.etree.ElementTree as ET

from scripts import assets


SVG_NS = {"svg": "http://www.w3.org/2000/svg"}


def _write_audit(path) -> None:
    fieldnames = ["event_year", "resolved", "exclusion_family"]
    rows = [
        {"event_year": "2012", "resolved": "True", "exclusion_family": "resolved"},
        {
            "event_year": "2013",
            "resolved": "False",
            "exclusion_family": "data_unavailability",
        },
        {
            "event_year": "2014",
            "resolved": "False",
            "exclusion_family": "model_inapplicability",
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _root(svg: str) -> ET.Element:
    return ET.fromstring(svg)


def test_load_audit_reads_repository_schema(tmp_path):
    audit = tmp_path / "audit.csv"
    _write_audit(audit)

    assert assets.load_audit(str(audit)) == [
        (2012, assets.RESOLVED),
        (2013, assets.UNREACHABLE),
        (2014, assets.INAPPLICABLE),
    ]


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
        assets.sample_field_svg(assets.demo_rows(), demo=True),
    ]

    for svg in svgs:
        root = _root(svg)
        assert len(root.findall("svg:title", SVG_NS)) == 1
        assert len(root.findall("svg:desc", SVG_NS)) == 1
