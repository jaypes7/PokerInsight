from pathlib import Path
from time import perf_counter

from app.parser.assembler import parse_hand

FIXTURE = Path(__file__).resolve().parents[4] / "packages" / "hh-fixtures" / "heads_up.txt"


def test_parser_throughput_smoke() -> None:
    raw = FIXTURE.read_text(encoding="utf-8")
    started = perf_counter()
    for _ in range(100):
        parse_hand(raw)
    elapsed = perf_counter() - started

    assert 100 / max(elapsed, 0.001) >= 100
