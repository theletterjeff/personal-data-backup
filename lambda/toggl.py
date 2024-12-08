from dataclasses import fields
from datetime import datetime, UTC
from typing import Any

import requests

from aws_sm import ApiKeyName, get_api_key
from aws_s3 import upload_records_to_s3
from handler_types import TimeEntry

url_root = "https://api.track.toggl.com/api/v9"
workspace_id = 2623046
headers = {"User-Agent": "jmartin-personal-data-backup/v0.0.1"}


def toggl_handler(start: int, end: int) -> dict[str, Any]:
    api_key = get_api_key(ApiKeyName.TOGGL)

    projects = {p["id"]: p["name"] for p in get_projects(api_key)}
    time_entries = [
        parse_time_entry(t, projects) for t in get_time_entries(start, end, api_key)
    ]

    s3_key = f"toggl/{start}_{end}.csv.gz"
    s3_bucket = "personaldatabackupstack-backupbucket26b8e51c-lvvadbyuciqx"
    fieldnames = [field.name for field in fields(TimeEntry)]
    return upload_records_to_s3(time_entries, fieldnames, s3_bucket, s3_key)


def get_projects(api_key: str):
    url = f"{url_root}/workspaces/{workspace_id}/projects"

    resp = requests.get(url, auth=(api_key, "api_token"), headers=headers)
    return resp.json()


def get_time_entries(start: int, end: int, api_key: str):
    url = f"{url_root}/me/time_entries"
    params = {
        "start_date": get_datestring(start),
        "end_date": get_datestring(end),
    }

    resp = requests.get(
        url, auth=(api_key, "api_token"), headers=headers, params=params
    )
    return resp.json()


def get_datestring(timestamp: int) -> str:
    utc_datetime = datetime.fromtimestamp(timestamp, UTC)
    return utc_datetime.strftime("%Y-%m-%d")


def parse_time_entry(resp_entry, projects: dict[int, str]) -> TimeEntry:
    return TimeEntry(
        id=resp_entry["id"],
        description=resp_entry["description"],
        duration=resp_entry["duration"],
        start=resp_entry["start"],
        stop=resp_entry["stop"],
        project_id=resp_entry["project_id"],
        project_name=projects[resp_entry["project_id"]],
        tag_ids=resp_entry["tag_ids"],
        tags=resp_entry["tags"],
    )
