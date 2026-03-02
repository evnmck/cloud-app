# backend/pipeline/error_handler.py
"""
Step Function error handler Lambda
Receives failures from Step Function and marks job as FAILED
"""
import json
from shared_services import update_job


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
