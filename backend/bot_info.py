"""Cached bot username for referral links."""
_bot_username: str = ""


def set_bot_username(username: str) -> None:
    global _bot_username
    _bot_username = username


def get_bot_username() -> str:
    return _bot_username
