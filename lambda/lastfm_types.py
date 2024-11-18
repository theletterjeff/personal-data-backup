from dataclasses import dataclass
from typing import TypedDict

class Event(TypedDict):
    """Both start and end should be UTC timestamps."""
    start: int
    end: int

@dataclass(frozen=True)
class PlayRecord:
    """IDs are MusicBrainz IDs"""
    date_timestamp: int
    date_readable: str
    artist_id: str
    artist_name: str
    track_id: str
    track_name: str
    album_id: str
    album_name: str