from pathlib import Path

import pytest

from app.parser.assembler import parse_hand
from app.parser.validator import validate

FIXTURES = Path(__file__).resolve().parents[4] / "packages" / "hh-fixtures"


@pytest.mark.property
def test_parsed_golden_fixtures_keep_core_invariants() -> None:
    for fixture in FIXTURES.glob("*.txt"):
        draft = parse_hand(fixture.read_text(encoding="utf-8"))

        assert validate(draft) == []
        assert draft.h_pfr <= draft.h_vpip
        assert draft.hero_position in {"BTN", "SB", "BB", "UTG", "MP", "CO", None}


@pytest.mark.property
def test_render_parse_round_trip_keeps_hand_id() -> None:
    fixture = FIXTURES / "heads_up.txt"
    raw = fixture.read_text(encoding="utf-8")

    first = parse_hand(raw)
    second = parse_hand(first.raw_text)

    assert second.site_hand_id == first.site_hand_id
