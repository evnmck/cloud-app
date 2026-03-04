"""
Utilities for Glue job operations.
Provides DynamoDB integration for updating job status.
"""

import os
from datetime import datetime, timezone
import boto3


dynamodb = boto3.resource("dynamodb")


def update_job_status(job_id: str, status: str, **extra_fields):
    """
    Update job record in DynamoDB with status and optional additional fields.
    
    Args:
        job_id: The job ID to update
        status: The new status (e.g., 'PROCESSED', 'FAILED', 'PENDING')
        **extra_fields: Additional fields to update (e.g., processedDataLocation, errorMessage)
        
    Example:
        update_job_status(
            job_id='abc-123',
            status='PROCESSED',
            processedDataLocation='s3://bucket/path/data.json'
        )
        
        update_job_status(
            job_id='abc-123',
            status='FAILED',
            errorMessage='Processing failed due to invalid data'
        )
    """
    jobs_table = dynamodb.Table(os.environ.get("JOBS_TABLE_NAME"))
    
    update_expr = 'SET #status = :status, updatedAt = :now'
    attr_names = {'#status': 'status'}
    attr_values = {
        ':status': status,
        ':now': datetime.now(timezone.utc).isoformat(),
    }
    
    # Add any extra fields to the update expression
    for i, (key, value) in enumerate(extra_fields.items()):
        update_expr += f', {key} = :val{i}'
        attr_values[f':val{i}'] = value
    
    jobs_table.update_item(
        Key={'jobId': job_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=attr_names,
        ExpressionAttributeValues=attr_values,
    )
