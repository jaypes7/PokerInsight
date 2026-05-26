from collections.abc import Iterable, Iterator

from app.parser.errors import ParseError


def decode_hand_history(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ParseError("BAD_ENCODING", "File is not valid UTF-8-SIG or CP1252")


def split_hands(lines: Iterable[str]) -> Iterator[list[str]]:
    buffer: list[str] = []
    seen_summary = False
    for raw_line in lines:
        line = raw_line.rstrip("\r\n")
        if line.strip() == "":
            if buffer and seen_summary:
                yield buffer
                buffer = []
                seen_summary = False
            continue
        buffer.append(line)
        if line.strip() == "*** SUMÁRIO ***" or line.strip() == "*** SUMÃRIO ***":
            seen_summary = True
    if buffer:
        yield buffer
