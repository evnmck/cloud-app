# backend/pipeline/error_handler.py
"""
Step Function error handler Lambda
Receives failures from Step Function and marks job as FAILED
"""
import json
import os
import boto3
from shared_services import update_job

lambda_client = boto3.client('lambda')

def handler(event, context):
    """Handle Step Function failure callbacks"""
    print(f"Step Function error: {json.dumps(event)[:500]}")
    
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
        
        print(f"Job {job_id} marked as FAILED: {error_message} in DB")

        try:
            lambda_client.invoke(
                FunctionName=os.environ['WEBSOCKET_SEND_UPDATE_ARN'],
                InvocationType='Event',  # Async invocation
                Payload=json.dumps({
                    "jobId": job_id,
                    "status": "FAILED",
                    "results": {"error": error_message[:1000]}  # Include error in WebSocket update
                }).encode('utf-8')
            )
            print(f"Invoked WebSocket update for FAILED job {job_id}")
        except Exception as e:
            print(f"Warning: Failed to send WebSocket update for FAILED job: {e}")
            # Continue even if WebSocket update fails
        
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
