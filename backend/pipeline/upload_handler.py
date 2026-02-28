# backend/pipeline/upload_handler.py
import os
import json
import boto3
from datetime import datetime, timezone
from shared_repositories import update_job_repository

JOBS_TABLE_NAME = os.environ["JOBS_TABLE_NAME"]
dynamodb = boto3.resource("dynamodb")
jobs_table = dynamodb.Table(JOBS_TABLE_NAME)
glue_client = boto3.client("glue")

def handler(event, context):
    print("S3 event:", json.dumps(event))

    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        print(f"Processing S3 object s3://{bucket}/{key}")

        # Expect "uploads/<jobId>/filename"
        parts = key.split("/")
        if len(parts) < 3 or parts[0] != "uploads":
            continue

        job_id = parts[1]

        now = datetime.now(timezone.utc).isoformat()

        update_job_repository(job_id, "UPLOADED")

        glue_client.start_job_run(
            JobName=os.environ["GLUE_JOB_NAME"],
            Arguments={
                "--jobId": job_id,
                "--bucket": bucket,
                "--key": key,
            }
        )

    return {"statusCode": 200, "body": "ok"}
