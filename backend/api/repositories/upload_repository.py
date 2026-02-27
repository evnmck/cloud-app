from config import Config
import boto3

dynamodb = boto3.resource("dynamodb")
jobs_table = dynamodb.Table(Config.JOBS_TABLE_NAME)

def create_upload_repository(job: dict):
    jobs_table.put_item(Item=job)

def get_job_repository(job_id: str) -> dict | None:
    resp = jobs_table.get_item(Key={"jobId": job_id})
    return resp.get("Item")