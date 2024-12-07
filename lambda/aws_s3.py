import csv
import io
from dataclasses import asdict
import gzip
import json
from typing import Any

import boto3

def upload_records_to_s3(
        records: list[Any],
        fieldnames: list[str],
        s3_bucket: str,
        s3_key: str,
) -> dict[str, Any]:
    csv_str = _get_csv_str(records, fieldnames)
    gzipped_csv = _get_gzipped_csv(csv_str)
    return _write_to_s3(gzipped_csv, s3_bucket, s3_key)

def _get_csv_str(records: list[Any], fieldnames: list[str]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for record in records:
        writer.writerow(asdict(record))
    return output.getvalue()

def _get_gzipped_csv(csv_content: str) -> io.BytesIO:
    gzipped_csv = io.BytesIO()
    with gzip.GzipFile(fileobj=gzipped_csv, mode="w") as gzipped_file:
        gzipped_file.write(csv_content.encode())

    gzipped_csv.seek(0)
    return gzipped_csv

def _write_to_s3(gzipped_csv: io.BytesIO, s3_bucket: str, s3_key: str) -> dict[str, Any]:
    s3_client = boto3.client("s3")
    s3_response = s3_client.put_object(
        Bucket=s3_bucket,
        Key=s3_key,
        Body=gzipped_csv.getvalue(),
        ContentType="text/csv",
        ContentEncoding="gzip",
    )

    if s3_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return {
                "status_code": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {"message": f"Successfully uploaded {s3_key} to {s3_bucket}"}
                )
        }
    else:
        return {
                "status_code": s3_response["ResponseMetadata"]["HTTPStatusCode"],
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {"message": f"Failed to upload {s3_key} to {s3_bucket}"}
                )
        }

