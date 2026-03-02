# backend/pipeline/upload_handler.py
"""
Multi-purpose Lambda handler:
1. S3 event trigger -> Start Step Function orchestration
2. Step Function failure callback -> Mark job as FAILED
"""
import os
import json
import boto3
from shared_services import update_job

stepfunctions = boto3.client("stepfunctions")

def handler(event, context):
    print(f"Event: {json.dumps(event)[:500]}")
    
    # Check if this is an S3 event or a Step Function failure callback
    if "Records" in event:
        # S3 event - trigger Step Function
        return handle_s3_upload(event)
    else:
        # Step Function failure callback - update job status
        return handle_job_failure(event)


def handle_s3_upload(event):
    """Handle S3 upload events"""
    print("Processing S3 upload event")
    
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        print(f"Processing S3 object s3://{bucket}/{key}")

        # Expect "uploads/<jobId>/filename"
        parts = key.split("/")
        if len(parts) < 3 or parts[0] != "uploads":
            continue

        job_id = parts[1]

        # Update job to PROCESSING
        update_job(job_id, "PROCESSING")

        # Trigger Step Function
        stepfunctions.start_execution(
            stateMachineArn=os.environ["STATE_MACHINE_ARN"],
            name=f"{job_id}-execution",
            input=json.dumps({
                "jobId": job_id,
                "bucket": bucket,
                "key": key,
            })
        )
        
        print(f"Step Function triggered for job {job_id}")
    
    return {
        'statusCode': 202,
        'body': json.dumps({'message': 'Processing initiated'})
    }


def handle_job_failure(event):
    """Handle Step Function failure callbacks"""
    print("Processing job failure")
    
    job_id = event.get('jobId')
    error = event.get('error', 'Unknown error')
    cause = event.get('cause', '')
    
    if not job_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing jobId'})
        }
    
    try:
        # Update job status to FAILED with error message
        error_message = f"{error}: {cause}".strip()
        update_job(
            job_id,
            'FAILED',
            error=error_message[:1000]  # Truncate to field limit
        )
        
        print(f"Job {job_id} marked as FAILED: {error_message}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Job marked as FAILED'})
        }
    except Exception as e:
        print(f"Error updating job status: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }



    return {"statusCode": 200, "body": "ok"}
