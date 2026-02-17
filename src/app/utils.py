"""Utility functions."""


def strtobool(val: str) -> bool:
    """Convert string to boolean."""
    val = val.lower()
    if val in ("y", "yes", "true", "t", "on", "1"):
        return True
    if val in ("n", "no", "false", "f", "off", "0"):
        return False
    raise ValueError(f"Invalid truth value: {val}")
