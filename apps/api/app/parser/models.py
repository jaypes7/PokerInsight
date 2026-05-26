from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

Street = Literal["preflop", "flop", "turn", "river", "showdown", "summary"]
ActionType = Literal[
    "fold",
    "check",
    "call",
    "bet",
    "raise",
    "post_blind",
    "post_ante",
    "shows",
    "mucks",
    "collect",
    "uncalled_return",
]


@dataclass(slots=True)
class SeatDraft:
    seat: int
    username: str
    starting_stack: int
    position: str | None = None
    is_hero: bool = False
    sit_out: bool = False
    posted_blind: str | None = None
    blind_amount: int = 0
    hole_cards: list[str] | None = None
    went_to_showdown: bool = False
    won_amount: int = 0
    final_action_street: str | None = None


@dataclass(slots=True)
class ActionDraft:
    sequence: int
    player_name: str
    street: Street
    action_type: ActionType
    amount: int = 0
    raise_to: int | None = None
    is_all_in: bool = False
    pot_before: int = 0
    pot_after: int = 0


@dataclass(slots=True)
class PotDraft:
    pot_index: int
    amount: int
    rake: int = 0
    winner_names: list[str] = field(default_factory=list)


@dataclass(slots=True)
class MetaEvent:
    line_no: int
    event_type: str
    player_name: str
    raw: str


@dataclass(slots=True)
class HandDraft:
    site_hand_id: str
    site_table_name: str
    table_max_players: int
    button_seat: int
    hero_username: str
    hero_seat: int | None
    played_at: datetime
    small_blind: int
    big_blind: int
    raw_text: str
    site: str = "pokerstars"
    site_tournament_id: str | None = None
    game_type: Literal["tournament", "cash", "sng", "spin"] = "tournament"
    variant: Literal["nlhe"] = "nlhe"
    buy_in_cents: int | None = None
    fee_cents: int | None = None
    currency: str = "USD"
    level_name: str | None = None
    ante: int = 0
    timezone_at_play: str | None = "ET"
    seats: list[SeatDraft] = field(default_factory=list)
    actions: list[ActionDraft] = field(default_factory=list)
    board: list[str] = field(default_factory=list)
    pots: list[PotDraft] = field(default_factory=list)
    rake: int = 0
    pot_total: int = 0
    parser_version: str = "1.0.0"
    meta_events: list[MetaEvent] = field(default_factory=list)
    hero_position: str | None = None
    hero_starting_stack: int | None = None
    hero_hole_cards: list[str] | None = None
    hero_net_cents: int | None = None
    hero_went_to_showdown: bool = False
    hero_won_at_showdown: bool | None = None
    h_saw_flop: bool = False
    h_saw_turn: bool = False
    h_saw_river: bool = False
    h_vpip: bool = False
    h_pfr: bool = False
    h_three_bet: bool = False
    h_faced_three_bet: bool = False
    h_folded_to_three_bet: bool = False
    h_pf_open: bool = False
    h_postflop_bets: int = 0
    h_postflop_raises: int = 0
    h_postflop_calls: int = 0
