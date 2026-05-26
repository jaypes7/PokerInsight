import re
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class Token:
    kind: str
    line_no: int
    raw: str
    groups: dict[str, str | None]


CARD: Final = r"[2-9TJQKA][hdcs]"
SECTION_HOLE = re.compile(r"^\*\*\* CARTAS DA MÃO \*\*\*\s*$")
SECTION_FLOP = re.compile(rf"^\*\*\* FLOP \*\*\* \[(?P<board>(?:{CARD} ?){{3}})\]\s*$")
SECTION_TURN = re.compile(
    rf"^\*\*\* TURN \*\*\* \[(?P<prev>(?:{CARD} ?){{3}})\] \[(?P<card>{CARD})\]\s*$"
)
SECTION_RIVER = re.compile(
    rf"^\*\*\* RIVER \*\*\* \[(?P<prev>(?:{CARD} ?){{4}})\] \[(?P<card>{CARD})\]\s*$"
)
SECTION_SHOWDOWN = re.compile(r"^\*\*\* SHOW DOWN \*\*\*\s*$")
SECTION_SUMMARY = re.compile(r"^\*\*\* SUMÁRIO \*\*\*\s*$")

HEADER_TOURNEY = re.compile(
    r"^Mão PokerStars #(?P<hand_id>\d+): "
    r"Torneio #(?P<tournament_id>\d+), "
    r"\$ ?(?P<buyin>\d+(?:[.,]\d+)?)\+\$ ?(?P<fee>\d+(?:[.,]\d+)?) "
    r"(?P<currency>[A-Z]{3}) (?P<variant>Hold'em No Limit) - "
    r"Nível (?P<level>[IVXLCDM]+) \((?P<sb>\d+)/(?P<bb>\d+)\) - "
    r"(?P<date>\d{4}/\d{2}/\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<tz>\S+)\s*$"
)
TABLE = re.compile(
    r"^Mesa '(?P<table>[^']+)' (?P<max>\d+)-max Lugar #(?P<button_seat>\d+) é o botão\s*$"
)
SEAT = re.compile(
    r"^Lugar (?P<seat>\d+): (?P<name>.+?) \((?P<chips>\d+) em fichas\)"
    r"(?P<sitout> está sit out)?\s*$"
)
ANTE = re.compile(r"^(?P<name>.+?): coloca ante (?P<amount>\d+)\s*$")
BLIND = re.compile(r"^(?P<name>.+?): paga o (?P<kind>small blind|big blind) (?P<amount>\d+)\s*$")
HERO_CARDS = re.compile(rf"^(?P<name>.+?) recebe \[(?P<c1>{CARD}) (?P<c2>{CARD})\]\s*$")
ACTION_FOLD = re.compile(r"^(?P<name>.+?): desiste\s*$")
ACTION_CHECK = re.compile(r"^(?P<name>.+?): passa\s*$")
ACTION_CALL = re.compile(r"^(?P<name>.+?): iguala (?P<amount>\d+)(?P<allin> e está all-in)?\s*$")
ACTION_BET = re.compile(r"^(?P<name>.+?): aposta (?P<amount>\d+)(?P<allin> e está all-in)?\s*$")
ACTION_RAISE = re.compile(
    r"^(?P<name>.+?): aumenta (?P<by>\d+) para (?P<to>\d+)(?P<allin> e está all-in)?\s*$"
)
UNCALLED = re.compile(r"^Aposta não-igualada \((?P<amount>\d+)\) voltou para (?P<name>.+?)\s*$")
COLLECT = re.compile(r"^(?P<name>.+?) recebeu (?P<amount>\d+) do pote\s*$")
SHOWS = re.compile(
    rf"^(?P<name>.+?): mostra \[(?P<c1>{CARD}) (?P<c2>{CARD})\] \((?P<desc>.+)\)\s*$"
)
MUCKS_HIDDEN = re.compile(r"^(?P<name>.+?): não mostra a mão\s*$")
MUCKS_REVEAL = re.compile(
    rf"^(?P<name>.+?): (?:esconde a mão|escondeu as cartas \[(?P<c1>{CARD}) (?P<c2>{CARD})\])\s*$"
)
CONN_SIT_OUT = re.compile(r"^(?P<name>.+?) está sit out\s*$")
CONN_DISCONN = re.compile(r"^(?P<name>.+?) está sem ligação\s*$")
CONN_RECONN = re.compile(r"^(?P<name>.+?) está ligado\s*$")
CONN_RETURNED = re.compile(r"^(?P<name>.+?) voltou\s*$")
CONN_TIMEOUT = re.compile(r"^(?P<name>.+?) gastou o tempo( enquanto estava sem ligação)?\s*$")
FINISH_PLACE = re.compile(r"^(?P<name>.+?) terminou o torneio em (?P<place>\d+)º lugar\s*$")
FINISH_PAID = re.compile(
    r"^(?P<name>.+?) Acabou o torneio em (?P<place>\d+)º lugar "
    r"e recebeu \$ ?(?P<amount>\d+\.\d+)\.?\s*$"
)
FINISH_WIN = re.compile(
    r"^(?P<name>.+?) ganhou o torneio e recebeu \$ ?(?P<amount>\d+\.\d+) - parabéns!\s*$"
)
SUM_TOTAL = re.compile(r"^Total pote (?P<pot>\d+) \| comissão (?P<rake>\d+)\s*$")
SUM_BOARD = re.compile(rf"^Mesa \[(?P<board>(?:{CARD} ?){{3,5}})\]\s*$")
SUM_SEAT = re.compile(
    r"^Lugar (?P<seat>\d+): (?P<name>.+?)(?: \((?P<role>Botão|small blind|big blind)\))?"
    r"(?: \((?P<role2>Botão|small blind|big blind)\))?(?P<outcome>.+)\s*$"
)

PATTERNS: Final[list[tuple[str, re.Pattern[str]]]] = [
    ("section_hole", SECTION_HOLE),
    ("section_flop", SECTION_FLOP),
    ("section_turn", SECTION_TURN),
    ("section_river", SECTION_RIVER),
    ("section_showdown", SECTION_SHOWDOWN),
    ("section_summary", SECTION_SUMMARY),
    ("header_tourney", HEADER_TOURNEY),
    ("table", TABLE),
    ("seat", SEAT),
    ("ante", ANTE),
    ("blind", BLIND),
    ("hero_cards", HERO_CARDS),
    ("action_fold", ACTION_FOLD),
    ("action_check", ACTION_CHECK),
    ("action_call", ACTION_CALL),
    ("action_bet", ACTION_BET),
    ("action_raise", ACTION_RAISE),
    ("uncalled", UNCALLED),
    ("collect", COLLECT),
    ("shows", SHOWS),
    ("mucks_hidden", MUCKS_HIDDEN),
    ("mucks_reveal", MUCKS_REVEAL),
    ("conn_sit_out", CONN_SIT_OUT),
    ("conn_disconn", CONN_DISCONN),
    ("conn_reconn", CONN_RECONN),
    ("conn_returned", CONN_RETURNED),
    ("conn_timeout", CONN_TIMEOUT),
    ("finish_place", FINISH_PLACE),
    ("finish_paid", FINISH_PAID),
    ("finish_win", FINISH_WIN),
    ("sum_total", SUM_TOTAL),
    ("sum_board", SUM_BOARD),
    ("sum_seat", SUM_SEAT),
]


def tokenize(line: str, line_no: int = 1) -> Token:
    normalized = line.replace("Ã£", "ã").replace("Ã©", "é").replace("Ã¡", "á")
    normalized = normalized.replace("Ã", "Á").replace("MÃ£o", "Mão")
    normalized = normalized.replace("NÃ­vel", "Nível").replace("SUMÃRIO", "SUMÁRIO")
    for kind, pattern in PATTERNS:
        match = pattern.match(normalized)
        if match:
            return Token(kind=kind, line_no=line_no, raw=normalized, groups=match.groupdict())
    return Token(kind="unknown", line_no=line_no, raw=normalized, groups={})
