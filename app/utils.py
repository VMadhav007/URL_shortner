import secrets

BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def generate_short_code(length: int = 7) -> str:
    return "".join(
        secrets.choice(BASE62)
        for _ in range(length)
    )