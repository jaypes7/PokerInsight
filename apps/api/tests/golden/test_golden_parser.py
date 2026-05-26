from pathlib import Path

import pytest

from app.parser.assembler import parse_hand

FIXTURES = Path(__file__).resolve().parents[4] / "packages" / "hh-fixtures"


@pytest.mark.parametrize("fixture_path", sorted(FIXTURES.glob("*.txt")), ids=lambda path: path.stem)
def test_golden_fixture_parses(fixture_path: Path) -> None:
    draft = parse_hand(fixture_path.read_text(encoding="utf-8-sig"))

    assert draft.site == "pokerstars"
    assert draft.site_hand_id
    assert draft.hero_username == "Hero"
    assert draft.seats
    assert draft.actions
    assert draft.pot_total >= 0


def test_showdown_fixture_sets_hero_flags() -> None:
    draft = parse_hand((FIXTURES / "showdown_simple.txt").read_text(encoding="utf-8"))

    assert draft.h_vpip is True
    assert draft.h_pfr is True
    assert draft.h_saw_flop is True
    assert draft.hero_won_at_showdown is True
