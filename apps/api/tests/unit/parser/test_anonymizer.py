import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[5] / "scripts"))

from anonymize_hh import anonymize

from app.parser.assembler import parse_hand


def test_anonymizer_is_deterministic_and_parseable() -> None:
    raw = (
        Path(__file__).resolve().parents[5] / "packages" / "hh-fixtures" / "heads_up.txt"
    ).read_text(encoding="utf-8")

    first = anonymize(raw, "Hero")
    second = anonymize(raw, "Hero")

    assert first == second
    assert "Player" in first
    assert parse_hand(first).hero_username == "Hero"
