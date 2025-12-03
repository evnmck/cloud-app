# backend/pipeline/upload_handler.py
import os
import json
import boto3
from datetime import datetime, timezone

JOBS_TABLE_NAME = os.environ["JOBS_TABLE_NAME"]
dynamodb = boto3.resource("dynamodb")
jobs_table = dynamodb.Table(JOBS_TABLE_NAME)

def handler(event, context):
    print("S3 event:", json.dumps(event))

    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        # Expect "uploads/<jobId>/filename"
        parts = key.split("/")
        if len(parts) < 3 or parts[0] != "uploads":
            continue

        job_id = parts[1]

        now = datetime.now(timezone.utc).isoformat()

        jobs_table.update_item(
            Key={"jobId": job_id},
            UpdateExpression="SET #st = :uploaded, updatedAt = :now",
            ExpressionAttributeNames={"#st": "status"},
            ExpressionAttributeValues={
                ":uploaded": "UPLOADED",
                ":now": now,
            },
        )

    return {"statusCode": 200, "body": "ok"}
