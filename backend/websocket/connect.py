import json
import boto3
import os
import time


def handler(event, context):
    """
    Called when WebSocket client connects.
    Store connectionId in DynamoDB with TTL.
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
        return {'statusCode': 200}
    except Exception as e:
        print(f"Error storing connection: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
