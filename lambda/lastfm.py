from datetime import datetime
from dataclasses import dataclass, fields
import logging

import requests
from aws_lambda_powertools.utilities.typing import LambdaContext

from aws.sm import ApiKeyName, get_api_key
from aws.s3 import upload_records_to_s3
from aws.lambdas import Event

logger = logging.getLogger()
logger.setLevel(level=logging.INFO)


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


def handler(event: Event, _: LambdaContext):
    start, end = event["start"], event["end"]
    logger.info(
        (
            f"backing up data for {unix_time_to_datestring(start)} "
            f"to {unix_time_to_datestring(end)}"
        )
    )

    api_key = get_api_key(ApiKeyName.LAST_FM)

    play_records: list[PlayRecord] = []
    page_num = 0

    while True:
        page_num += 1
        page = get_page(start, end, page_num, api_key)
        records = get_records(page)

        if len(records) == 0:
            break

        for record in records:
            play_record = parse_data(record)
            play_records.append(play_record)

    s3_key = f"lastfm/{start}_{end}.csv.gz"
    s3_bucket = "personaldatabackupstack-backupbucket26b8e51c-lvvadbyuciqx"
    fieldnames = [field.name for field in fields(PlayRecord)]
    return upload_records_to_s3(play_records, fieldnames, s3_bucket, s3_key)


def unix_time_to_datestring(unix_time: int) -> str:
    dt = datetime.fromtimestamp(unix_time)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_page(start: int, end: int, page_num: int, api_key: str):
    url = "http://ws.audioscrobbler.com/2.0/"
    headers = {
        "User-Agent": "jmartin87-personal-data-backup/v0.0.1",
    }
    params = {
        "method": "user.getrecenttracks",
        "api_key": api_key,
        "format": "json",
        "user": "jmartin87",
        "from": start,
        "to": end,
        "page": page_num,
        "limit": 200,
    }
    resp = requests.get(url=url, headers=headers, params=params)
    return resp.json()


def get_records(page):
    return page["recenttracks"]["track"]


def parse_data(record) -> PlayRecord:
    return PlayRecord(
        date_timestamp=record["date"]["uts"],
        date_readable=record["date"]["#text"],
        artist_id=record["artist"]["mbid"],
        artist_name=record["artist"]["#text"],
        track_id=record["mbid"],
        track_name=record["name"],
        album_id=record["album"]["mbid"],
        album_name=record["album"]["#text"],
    )
