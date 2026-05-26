from datetime import UTC, datetime

from app.parser.models import ActionDraft, HandDraft, PotDraft, SeatDraft
from app.parser.validator import validate


def test_validate_reports_all_supported_invariants() -> None:
    draft = HandDraft(
        site_hand_id="1",
        site_table_name="T",
        table_max_players=2,
        button_seat=9,
        hero_username="Hero",
        hero_seat=None,
        played_at=datetime(1999, 1, 1, tzinfo=UTC),
        small_blind=50,
        big_blind=100,
        raw_text="raw",
        seats=[
            SeatDraft(1, "Villain", 1000, hole_cards=["Ah", "Kd"]),
            SeatDraft(2, "Villain", 1000, hole_cards=["Ah", "Qc"]),
        ],
        actions=[ActionDraft(1, "Villain", "flop", "check")],
        board=["2c", "3d", "4h"],
        pots=[PotDraft(0, 500)],
        pot_total=100,
    )

    codes = {violation.code for violation in validate(draft)}

    assert codes == {
        "MISSING_HERO",
        "BAD_BUTTON",
        "DUPLICATE_PLAYER",
        "NO_PREFLOP_ACTION",
        "POT_MISMATCH",
        "CARD_DUPLICATE",
        "BAD_TIMESTAMP",
    }


def test_validate_requires_seats() -> None:
    draft = HandDraft(
        site_hand_id="1",
        site_table_name="T",
        table_max_players=2,
        button_seat=1,
        hero_username="Hero",
        hero_seat=None,
        played_at=datetime(2026, 1, 1, tzinfo=UTC),
        small_blind=50,
        big_blind=100,
        raw_text="raw",
        actions=[ActionDraft(1, "Hero", "preflop", "fold")],
    )

    assert [violation.code for violation in validate(draft)] == [
        "MISSING_SEATS",
        "MISSING_HERO",
        "BAD_BUTTON",
    ]
