from pathlib import Path

from app.parser.splitter import decode_hand_history, split_hands

FIXTURES = Path(__file__).resolve().parents[5] / "packages" / "hh-fixtures"


def test_splitter_handles_multiple_hands_and_blank_lines() -> None:
    first = (FIXTURES / "walk_bb.txt").read_text(encoding="utf-8")
    second = (FIXTURES / "heads_up.txt").read_text(encoding="utf-8")

    chunks = list(split_hands((first + "\r\n\r\n" + second + "\n").splitlines()))

    assert len(chunks) == 2
    assert chunks[0][0].startswith("Mão PokerStars")
    assert chunks[1][0].startswith("Mão PokerStars")


def test_decode_supports_utf8_sig_and_cp1252() -> None:
    text = (FIXTURES / "walk_bb.txt").read_text(encoding="utf-8")

    assert decode_hand_history(("\ufeff" + text).encode("utf-8")).startswith("Mão")
    assert decode_hand_history(text.encode("cp1252")).startswith("Mão")
