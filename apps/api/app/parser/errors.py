from dataclasses import dataclass


@dataclass
class ParseError(Exception):
    code: str
    message: str
    line_start: int = 1
    line_end: int = 1
    raw_excerpt: str = ""

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


@dataclass(frozen=True)
class InvariantViolation:
    code: str
    message: str
    line_start: int = 1
    line_end: int = 1
