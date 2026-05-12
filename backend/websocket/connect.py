import json
import boto3
import os
import time


def handler(event, context):
    """
    Called when WebSocket client connects.
    Store connectionId in DynamoDB with TTL.
    
    TODO (Part of EV-0002 - Authentication System):
    - Validate JWT token from query string parameters
    - Extract userId from JWT token
    - Store userId alongside connectionId for per-user filtering
    - Return 401 for unauthorized connections
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['WEBSOCKET_CONNECTIONS_TABLE'])
    
    connection_id = event['requestContext']['connectionId']
    timestamp = int(time.time())
    ttl = timestamp + 86400  # 24 hour expiry
    
    try:
        table.put_item(Item={
            'connectionId': connection_id,
            'connected_at': timestamp,
            'ttl': ttl
        })
        print(f"Connection stored: {connection_id}")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'connectionId': connection_id,
                'message': 'Connected successfully'
            })
        }
    except Exception as e:
        print(f"Error storing connection: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
