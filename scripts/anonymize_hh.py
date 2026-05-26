from __future__ import annotations

import re
import sys
from pathlib import Path

NAME_PATTERNS = [
    re.compile(r"^Lugar \d+: (?P<name>.+?) \("),
    re.compile(r"^(?P<name>.+?): "),
    re.compile(r"^(?P<name>.+?) recebeu "),
    re.compile(r"voltou para (?P<name>.+?)\s*$"),
]


def anonymize(text: str, hero: str | None = None) -> str:
    names = _discover_names(text)
    mapping: dict[str, str] = {}
    index = 1
    for name in names:
        if hero and name == hero:
            mapping[name] = "Hero"
        else:
            mapping[name] = f"Player{index}"
            index += 1
    output = text
    for original, replacement in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True):
        output = output.replace(original, replacement)
    return output


def _discover_names(text: str) -> list[str]:
    names: list[str] = []
    for line in text.splitlines():
        if line.startswith("Mão PokerStars #"):
            continue
        for pattern in NAME_PATTERNS:
            match = pattern.search(line)
            if match:
                name = match.group("name")
                if name not in names and not name.startswith("***"):
                    names.append(name)
                break
    return names


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: anonymize_hh.py FILE [HERO]", file=sys.stderr)
        return 2
    path = Path(argv[1])
    hero = argv[2] if len(argv) > 2 else None
    sys.stdout.write(anonymize(path.read_text(encoding="utf-8-sig"), hero))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
