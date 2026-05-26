from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class UserFactory:
    email: str
    display_name: str
    password_hash: str
    locale: str = "pt-BR"

    @classmethod
    def build(cls) -> "UserFactory":
        suffix = uuid4().hex[:8]
        return cls(
            email=f"hero-{suffix}@example.com",
            display_name="Hero",
            password_hash="pbkdf2_sha256$390000$fixture",
        )


def make_hero_user() -> UserFactory:
    return UserFactory.build()
