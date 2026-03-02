# backend/pipeline/upload_trigger.py
"""
S3 trigger Lambda
Receives S3 upload events, updates job to PROCESSING, and triggers Step Function
"""
import os
import json
import boto3
from shared_services import update_job

stepfunctions = boto3.client("stepfunctions")


def handler(event, context):
    """Handle S3 upload events"""
    print(f"S3 event: {json.dumps(event)[:500]}")
    
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        print(f"Processing S3 object s3://{bucket}/{key}")

        # Expect "uploads/<jobId>/filename"
        parts = key.split("/")
        if len(parts) < 3 or parts[0] != "uploads":
            continue

        job_id = parts[1]

        try:
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
        except Exception as e:
            print(f"Error processing S3 event: {str(e)}")
            # Update job status to FAILED on error
            try:
                update_job(job_id, "FAILED", error=f"Upload trigger error: {str(e)[:900]}")
            except Exception as update_err:
                print(f"Failed to update job status: {str(update_err)}")
            raise
    
    return {
        'statusCode': 202,
        'body': json.dumps({'message': 'Processing initiated'})
    }
