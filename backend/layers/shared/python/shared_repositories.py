
from datetime import datetime, timezone
import os
import boto3

dynamodb = boto3.resource("dynamodb")
jobs_table = dynamodb.Table(os.environ["JOBS_TABLE_NAME"])

def update_job_repository(job_id: str, status: str):
    jobs_table.update_item(
        Key={"jobId": job_id},
        UpdateExpression="SET #st = :status, updatedAt = :now",
        ExpressionAttributeNames={"#st": "status"},
        ExpressionAttributeValues={
            ":status": status,
            ":now": datetime.now(timezone.utc).isoformat(),
        },
    )