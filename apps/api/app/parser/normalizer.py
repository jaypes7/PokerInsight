from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.parser.models import ActionDraft, HandDraft, SeatDraft

NEW_YORK = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


def money_to_cents(value: str) -> int:
    return int((Decimal(value.replace(",", ".")) * 100).quantize(Decimal("1")))


def parse_played_at(date: str, time: str) -> datetime:
    local = datetime.strptime(f"{date} {time}", "%Y/%m/%d %H:%M:%S").replace(tzinfo=NEW_YORK)
    return local.astimezone(UTC)


def cards_from_text(text: str) -> list[str]:
    return [card for card in text.split(" ") if card]


def assign_positions(hand: HandDraft) -> None:
    active = [seat for seat in hand.seats if not seat.sit_out or seat.blind_amount > 0]
    active.sort(key=lambda seat: seat.seat)
    if not active:
        return

    button_index = next(
        (idx for idx, seat in enumerate(active) if seat.seat == hand.button_seat),
        0,
    )
    ordered = active[button_index + 1 :] + active[: button_index + 1]
    names = _position_names(len(active))
    for seat, position in zip(ordered, names, strict=False):
        seat.position = position
    if len(active) == 2:
        active[button_index].position = "BTN"
        ordered[0].position = "SB"
        ordered[1].position = "BB"

    hero = next((seat for seat in hand.seats if seat.username == hand.hero_username), None)
    if hero is not None:
        hand.hero_position = hero.position
        hand.hero_starting_stack = hero.starting_stack


def compute_action_pots(hand: HandDraft) -> None:
    pot = 0
    committed: dict[tuple[str, str], int] = {}
    for action in hand.actions:
        action.pot_before = pot
        key = (action.street, action.player_name)
        contribution = 0
        if action.action_type in {"post_ante", "post_blind", "call", "bet"}:
            contribution = action.amount
            committed[key] = committed.get(key, 0) + contribution
        elif action.action_type == "raise" and action.raise_to is not None:
            previous = committed.get(key, 0)
            contribution = max(action.raise_to - previous, 0)
            committed[key] = action.raise_to
            action.amount = contribution
        elif action.action_type == "uncalled_return":
            contribution = -action.amount
        pot += contribution
        action.pot_after = max(pot, 0)


def derive_hero_flags(hand: HandDraft) -> None:
    hero_actions = [action for action in hand.actions if action.player_name == hand.hero_username]
    preflop = [action for action in hero_actions if action.street == "preflop"]
    postflop = [action for action in hero_actions if action.street in {"flop", "turn", "river"}]
    hand.h_vpip = any(action.action_type in {"call", "bet", "raise"} for action in preflop)
    hand.h_pfr = any(action.action_type in {"bet", "raise"} for action in preflop)
    hand.h_pf_open = _hero_opened_preflop(hand)
    hand.h_three_bet = _hero_three_bet(hand)
    hand.h_faced_three_bet, hand.h_folded_to_three_bet = _hero_faced_three_bet(hand)
    hand.h_saw_flop = bool(hand.board) and not _folded_on_or_before(hero_actions, "preflop")
    hand.h_saw_turn = len(hand.board) >= 4 and not _folded_on_or_before(hero_actions, "flop")
    hand.h_saw_river = len(hand.board) >= 5 and not _folded_on_or_before(hero_actions, "turn")
    hand.h_postflop_bets = sum(1 for action in postflop if action.action_type == "bet")
    hand.h_postflop_raises = sum(1 for action in postflop if action.action_type == "raise")
    hand.h_postflop_calls = sum(1 for action in postflop if action.action_type == "call")
    hand.hero_went_to_showdown = any(action.action_type == "shows" for action in hero_actions)
    hand.hero_won_at_showdown = any(
        action.action_type == "collect" and action.player_name == hand.hero_username
        for action in hand.actions
    )
    winnings = sum(
        action.amount
        for action in hand.actions
        if action.player_name == hand.hero_username and action.action_type == "collect"
    )
    invested = sum(
        action.amount
        for action in hero_actions
        if action.action_type in {"post_ante", "post_blind", "call", "bet", "raise"}
    )
    hand.hero_net_cents = winnings - invested


def _position_names(count: int) -> list[str]:
    if count <= 2:
        return ["SB", "BB"]
    if count <= 6:
        return ["SB", "BB", "UTG", "MP", "CO", "BTN"][-count:]
    return ["SB", "BB", "UTG", "UTG+1", "UTG+2", "MP", "MP+1", "CO", "BTN"][-count:]


def _folded_on_or_before(actions: list[ActionDraft], street: str) -> bool:
    order = {"preflop": 0, "flop": 1, "turn": 2, "river": 3}
    return any(
        action.action_type == "fold" and order.get(action.street, 99) <= order[street]
        for action in actions
    )


def _hero_opened_preflop(hand: HandDraft) -> bool:
    raises_before = 0
    for action in hand.actions:
        if action.street != "preflop":
            continue
        if action.player_name == hand.hero_username and action.action_type in {"bet", "raise"}:
            return raises_before == 0
        if action.action_type in {"bet", "raise"}:
            raises_before += 1
    return False


def _hero_three_bet(hand: HandDraft) -> bool:
    raises_before = 0
    for action in hand.actions:
        if action.street != "preflop":
            continue
        if action.player_name == hand.hero_username and action.action_type == "raise":
            return raises_before == 1
        if action.action_type in {"bet", "raise"}:
            raises_before += 1
    return False


def _hero_faced_three_bet(hand: HandDraft) -> tuple[bool, bool]:
    if not hand.h_pf_open:
        return False, False
    seen_hero_open = False
    faced = False
    for action in hand.actions:
        if action.street != "preflop":
            continue
        if action.player_name == hand.hero_username and action.action_type in {"bet", "raise"}:
            seen_hero_open = True
            continue
        if (
            seen_hero_open
            and action.player_name != hand.hero_username
            and action.action_type == "raise"
        ):
            faced = True
            continue
        if faced and action.player_name == hand.hero_username:
            return True, action.action_type == "fold"
    return faced, False


def find_hero_seat(seats: list[SeatDraft], hero_username: str) -> int | None:
    hero = next((seat for seat in seats if seat.username == hero_username), None)
    return hero.seat if hero is not None else None
