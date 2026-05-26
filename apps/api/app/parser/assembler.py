from app.parser.errors import ParseError
from app.parser.models import ActionDraft, HandDraft, MetaEvent, PotDraft, SeatDraft
from app.parser.normalizer import (
    assign_positions,
    cards_from_text,
    compute_action_pots,
    derive_hero_flags,
    find_hero_seat,
    money_to_cents,
    parse_played_at,
)
from app.parser.tokenizer import Token, tokenize
from app.parser.validator import validate


def parse_hand(raw_hand: str, parser_version: str = "1.0.0") -> HandDraft:
    lines = [line for line in raw_hand.splitlines() if line.strip()]
    if not lines:
        raise ParseError("MISSING_HEADER", "Empty hand")
    tokens = [tokenize(line, index + 1) for index, line in enumerate(lines)]
    if tokens[0].kind != "header_tourney":
        raise _error(tokens[0], "MISSING_HEADER", "Hand must start with PokerStars header")
    if len(tokens) < 2 or tokens[1].kind != "table":
        raise _error(tokens[min(1, len(tokens) - 1)], "UNKNOWN_LINE", "Missing table line")

    header = tokens[0].groups
    table = tokens[1].groups
    seats: list[SeatDraft] = []
    actions: list[ActionDraft] = []
    meta_events: list[MetaEvent] = []
    board: list[str] = []
    pots: list[PotDraft] = []
    street = "preflop"
    sequence = 0
    ante = 0
    hero_username = ""
    hero_cards: list[str] | None = None
    pot_total = 0
    rake = 0
    index = 2

    while index < len(tokens) and tokens[index].kind == "seat":
        group = tokens[index].groups
        seats.append(
            SeatDraft(
                seat=int(_required(group, "seat")),
                username=_required(group, "name"),
                starting_stack=int(_required(group, "chips")),
                sit_out=group.get("sitout") is not None,
            )
        )
        index += 1

    while index < len(tokens):
        token = tokens[index]
        group = token.groups
        if token.kind == "ante":
            sequence += 1
            amount = int(_required(group, "amount"))
            ante = max(ante, amount)
            actions.append(
                ActionDraft(sequence, _required(group, "name"), "preflop", "post_ante", amount)
            )
        elif token.kind == "blind":
            sequence += 1
            amount = int(_required(group, "amount"))
            name = _required(group, "name")
            kind = "sb" if _required(group, "kind") == "small blind" else "bb"
            _mark_blind(seats, name, kind, amount)
            actions.append(ActionDraft(sequence, name, "preflop", "post_blind", amount))
        elif token.kind == "section_hole":
            pass
        elif token.kind == "hero_cards":
            hero_username = _required(group, "name")
            hero_cards = [_required(group, "c1"), _required(group, "c2")]
            _mark_hole_cards(seats, hero_username, hero_cards, is_hero=True)
        elif token.kind == "section_flop":
            street = "flop"
            board = cards_from_text(_required(group, "board"))
        elif token.kind == "section_turn":
            street = "turn"
            board = cards_from_text(_required(group, "prev")) + [_required(group, "card")]
        elif token.kind == "section_river":
            street = "river"
            board = cards_from_text(_required(group, "prev")) + [_required(group, "card")]
        elif token.kind == "section_showdown":
            street = "showdown"
        elif token.kind.startswith("action_"):
            sequence += 1
            actions.append(_action_from_token(sequence, street, token))
        elif token.kind == "uncalled":
            sequence += 1
            actions.append(
                ActionDraft(
                    sequence,
                    _required(group, "name"),
                    street,  # type: ignore[arg-type]
                    "uncalled_return",
                    int(_required(group, "amount")),
                )
            )
        elif token.kind == "collect":
            sequence += 1
            name = _required(group, "name")
            amount = int(_required(group, "amount"))
            _mark_winner(seats, name, amount)
            actions.append(ActionDraft(sequence, name, street, "collect", amount))  # type: ignore[arg-type]
        elif token.kind == "shows":
            sequence += 1
            name = _required(group, "name")
            cards = [_required(group, "c1"), _required(group, "c2")]
            _mark_hole_cards(seats, name, cards, is_hero=name == hero_username)
            _mark_showdown(seats, name)
            actions.append(ActionDraft(sequence, name, "showdown", "shows"))
        elif token.kind in {"mucks_hidden", "mucks_reveal"}:
            sequence += 1
            name = _required(group, "name")
            if group.get("c1") and group.get("c2"):
                _mark_hole_cards(seats, name, [_required(group, "c1"), _required(group, "c2")])
            actions.append(ActionDraft(sequence, name, "showdown", "mucks"))
        elif token.kind.startswith("conn_"):
            meta_events.append(
                MetaEvent(token.line_no, token.kind, _required(group, "name"), token.raw)
            )
        elif token.kind == "sum_total":
            pot_total = int(_required(group, "pot"))
            rake = int(_required(group, "rake"))
        elif token.kind == "sum_board":
            board = cards_from_text(_required(group, "board"))
        elif token.kind in {
            "sum_seat",
            "finish_place",
            "finish_paid",
            "finish_win",
            "section_summary",
        }:
            pass
        elif token.kind == "unknown":
            raise _error(token, "UNKNOWN_LINE", f"Unsupported line: {token.raw}")
        index += 1

    if not hero_username:
        raise ParseError("MISSING_HERO", "Hero cards line was not found")
    hero_seat = find_hero_seat(seats, hero_username)
    draft = HandDraft(
        site_hand_id=_required(header, "hand_id"),
        site_tournament_id=_required(header, "tournament_id"),
        site_table_name=_required(table, "table"),
        table_max_players=int(_required(table, "max")),
        button_seat=int(_required(table, "button_seat")),
        hero_username=hero_username,
        hero_seat=hero_seat,
        played_at=parse_played_at(_required(header, "date"), _required(header, "time")),
        buy_in_cents=money_to_cents(_required(header, "buyin")),
        fee_cents=money_to_cents(_required(header, "fee")),
        currency=_required(header, "currency"),
        level_name=_required(header, "level"),
        small_blind=int(_required(header, "sb")),
        big_blind=int(_required(header, "bb")),
        ante=ante,
        seats=seats,
        actions=actions,
        board=board,
        pots=pots,
        rake=rake,
        pot_total=pot_total,
        raw_text=raw_hand,
        parser_version=parser_version,
        meta_events=meta_events,
        hero_hole_cards=hero_cards,
    )
    if pot_total:
        winners = [seat.username for seat in seats if seat.won_amount > 0]
        draft.pots.append(PotDraft(0, pot_total, rake, winners))
    assign_positions(draft)
    compute_action_pots(draft)
    derive_hero_flags(draft)
    violations = validate(draft)
    if violations:
        violation = violations[0]
        raise ParseError(
            violation.code, violation.message, violation.line_start, violation.line_end
        )
    return draft


def _action_from_token(sequence: int, street: str, token: Token) -> ActionDraft:
    group = token.groups
    name = _required(group, "name")
    action_map = {
        "action_fold": "fold",
        "action_check": "check",
        "action_call": "call",
        "action_bet": "bet",
        "action_raise": "raise",
    }
    action_type = action_map[token.kind]
    amount = int(group.get("amount") or group.get("by") or 0)
    raise_to = int(_required(group, "to")) if group.get("to") else None
    return ActionDraft(
        sequence,
        name,
        street,  # type: ignore[arg-type]
        action_type,  # type: ignore[arg-type]
        amount,
        raise_to,
        group.get("allin") is not None,
    )


def _required(group: dict[str, str | None], key: str) -> str:
    value = group.get(key)
    if value is None:
        raise ParseError("UNKNOWN_LINE", f"Missing regex group {key}")
    return value


def _error(token: Token, code: str, message: str) -> ParseError:
    return ParseError(code, message, token.line_no, token.line_no, token.raw)


def _mark_blind(seats: list[SeatDraft], name: str, kind: str, amount: int) -> None:
    seat = next((candidate for candidate in seats if candidate.username == name), None)
    if seat is not None:
        seat.posted_blind = kind
        seat.blind_amount += amount


def _mark_hole_cards(
    seats: list[SeatDraft],
    name: str,
    cards: list[str],
    is_hero: bool = False,
) -> None:
    seat = next((candidate for candidate in seats if candidate.username == name), None)
    if seat is not None:
        seat.hole_cards = cards
        seat.is_hero = seat.is_hero or is_hero


def _mark_showdown(seats: list[SeatDraft], name: str) -> None:
    seat = next((candidate for candidate in seats if candidate.username == name), None)
    if seat is not None:
        seat.went_to_showdown = True
        seat.final_action_street = "showdown"


def _mark_winner(seats: list[SeatDraft], name: str, amount: int) -> None:
    seat = next((candidate for candidate in seats if candidate.username == name), None)
    if seat is not None:
        seat.won_amount += amount
