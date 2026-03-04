import json
import boto3
import os


def handler(event, context):
    """
    Called when WebSocket client disconnects.
    Remove connectionId from DynamoDB.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['WEBSOCKET_CONNECTIONS_TABLE'])
    
    connection_id = event['requestContext']['connectionId']
    
    try:
        table.delete_item(Key={'connectionId': connection_id})
        print(f"Connection deleted: {connection_id}")
        return {'statusCode': 200}
    except Exception as e:
        print(f"Error deleting connection: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
