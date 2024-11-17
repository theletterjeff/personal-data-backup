import csv
import gzip
from dataclasses import asdict, dataclass, fields
import io
import json
from typing import TypedDict

from aws_lambda_powertools.utilities.typing import LambdaContext
import boto3
import requests

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

class Event(TypedDict):
    """Both start and end should be UTC timestamps."""
    start: int
    end: int

def handler(event: Event, _: LambdaContext):
    start, end = event["start"], event["end"]
    api_key = get_api_key()

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

    csv_str = get_csv_str(play_records)
    gzipped_csv = get_gzipped_csv(csv_str)
    filename = f'{start}_{end}.csv.gz'
    write_to_s3(gzipped_csv, filename)

    return {
        "status_code": 200,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps({
            "filesize": len(csv_str),
        }),
    }

def get_api_key():
    secret_name = "personal-backup-keys"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    sm_client = session.client(
        service_name='secretsmanager',
        region_name=region_name,
    )

    secret_resp = sm_client.get_secret_value(SecretId=secret_name)
    secret = json.loads(secret_resp["SecretString"])
    return secret["last_fm_api_key"]


def get_csv_str(records: list[PlayRecord]) -> str:
    output = io.StringIO()
    fieldnames = [field.name for field in fields(PlayRecord)]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for record in records:
        writer.writerow(asdict(record))
    return output.getvalue()

def get_gzipped_csv(csv_content: str) -> io.BytesIO:
    gzipped_csv = io.BytesIO()
    with gzip.GzipFile(fileobj=gzipped_csv, mode="w") as gzipped_file:
        gzipped_file.write(csv_content.encode())

    gzipped_csv.seek(0)
    return gzipped_csv

def write_to_s3(gzipped_csv: io.BytesIO, filename: str) -> None:
    s3_client = boto3.client("s3")
    s3_bucket = "personaldatabackupstack-backupbucket26b8e51c-lvvadbyuciqx"
    s3_key = f"lastfm/{filename}"
    s3_response = s3_client.put_object(
        Bucket=s3_bucket,
        Key=s3_key,
        Body=gzipped_csv.getvalue(),
        ContentType="text/csv",
        ContentEncoding="gzip",
    )

    if s3_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print(f'Successfully uploaded {s3_key} to {s3_bucket}')
    else:
     print(f'Failed to upload {s3_key} to {s3_bucket}')

def get_records(page):
    return page["recenttracks"]["track"]

def parse_data(record) -> PlayRecord:
    return PlayRecord(
        date_timestamp = record["date"]["uts"],
        date_readable = record["date"]["#text"],
        artist_id = record["artist"]["mbid"],
        artist_name = record["artist"]["#text"],
        track_id = record["mbid"],
        track_name = record["name"],
        album_id = record["album"]["mbid"],
        album_name = record["album"]["#text"],
    )

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
