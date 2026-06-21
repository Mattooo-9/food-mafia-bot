import re

# User-friendly TON address (bounceable / non-bounceable).
_TON_ADDRESS = re.compile(r"^(UQ|EQ|kQ|0Q)[A-Za-z0-9_-]{46}$")


def is_valid_ton_address(address: str) -> bool:
    return bool(_TON_ADDRESS.match(address.strip()))
