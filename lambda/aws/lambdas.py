from typing import TypedDict


class Event(TypedDict):
    """Both start and end should be UTC timestamps."""

    start: int
    end: int
