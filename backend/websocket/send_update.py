import json
import boto3
import os
import time


def handler(event, context):
    """
    Called by Step Function when job completes.
    Send status update to all connected WebSocket clients.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['WEBSOCKET_CONNECTIONS_TABLE'])
    apigw_client = boto3.client('apigatewaymanagementapi',
        endpoint_url=os.environ['WEBSOCKET_ENDPOINT']
    )
    
    job_id = event['jobId']
    status = event['status']
    results = event.get('results')
    
    # Prepare message
    message = {
        'type': 'job_update',
        'jobId': job_id,
        'status': status,
        'timestamp': int(time.time()),
    }
    
    if results:
        message['results'] = results
    
    # Get all active connections
    try:
        response = table.scan()
        connections = response.get('Items', [])
        
        failed_connections = []
        
        print(f"Broadcasting to {len(connections)} connected clients")
        
        # Broadcast to all connections
        for conn in connections:
            connection_id = conn['connectionId']
            try:
                apigw_client.post_to_connection(
                    ConnectionId=connection_id,
                    Data=json.dumps(message).encode('utf-8')
                )
                print(f"Sent to {connection_id}")
            except apigw_client.exceptions.GoneException:
                # Connection closed, mark for deletion
                print(f"Connection gone: {connection_id}")
                failed_connections.append(connection_id)
            except Exception as e:
                print(f"Error sending to {connection_id}: {e}")
        
        # Clean up gone connections
        for conn_id in failed_connections:
            table.delete_item(Key={'connectionId': conn_id})
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Broadcast complete',
                'connections_notified': len(connections) - len(failed_connections),
                'cleaned_up': len(failed_connections)
            })
        }
    
    except Exception as e:
        print(f"Error broadcasting: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
