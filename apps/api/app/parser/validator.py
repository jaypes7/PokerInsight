from app.parser.errors import InvariantViolation
from app.parser.models import HandDraft


def validate(draft: HandDraft) -> list[InvariantViolation]:
    violations: list[InvariantViolation] = []
    if not draft.seats:
        violations.append(InvariantViolation("MISSING_SEATS", "Hand has no seats"))
    if draft.hero_username and all(seat.username != draft.hero_username for seat in draft.seats):
        violations.append(InvariantViolation("MISSING_HERO", "Hero does not appear in seats"))
    if all(seat.seat != draft.button_seat for seat in draft.seats):
        violations.append(InvariantViolation("BAD_BUTTON", "Button seat does not exist"))
    if len({seat.username for seat in draft.seats}) != len(draft.seats):
        violations.append(InvariantViolation("DUPLICATE_PLAYER", "Duplicate player in seats"))
    if not any(action.street == "preflop" for action in draft.actions):
        violations.append(InvariantViolation("NO_PREFLOP_ACTION", "Hand has no preflop action"))
    if draft.pot_total < sum(pot.amount for pot in draft.pots):
        violations.append(InvariantViolation("POT_MISMATCH", "Pots exceed summary total"))
    cards: list[str] = list(draft.board)
    for seat in draft.seats:
        if seat.hole_cards:
            cards.extend(seat.hole_cards)
    if len(cards) != len(set(cards)):
        violations.append(InvariantViolation("CARD_DUPLICATE", "Card appears more than once"))
    if not (2000 <= draft.played_at.year <= 2100):
        violations.append(
            InvariantViolation("BAD_TIMESTAMP", "Timestamp is out of supported range")
        )
    return violations
