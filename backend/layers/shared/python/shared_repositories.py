from datetime import datetime, timezone
import os
import boto3

dynamodb = boto3.resource("dynamodb")
jobs_table = dynamodb.Table(os.environ["JOBS_TABLE_NAME"])

def update_job_repository(job_id: str, status: str, **extra_fields):
    """Update job status and any additional fields in DynamoDB"""
    update_expr = 'SET #status = :status, updatedAt = :now'
    attr_names = {'#status': 'status'}
    attr_values = {
        ':status': status,
        ':now': datetime.now(timezone.utc).isoformat(),
    }
    
    for i, (key, value) in enumerate(extra_fields.items()):
        update_expr += f', {key} = :val{i}'
        attr_values[f':val{i}'] = value
    
    jobs_table.update_item(
        Key={'jobId': job_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=attr_names,
        ExpressionAttributeValues=attr_values,
    )