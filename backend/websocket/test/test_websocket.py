import json
import boto3
import pytest
import os
import sys
from moto import mock_dynamodb
from unittest.mock import patch, MagicMock
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import handlers
import connect
import disconnect
import send_update

connect_handler = connect.handler
disconnect_handler = disconnect.handler
send_update_handler = send_update.handler


@mock_dynamodb
def test_websocket_connect_stores_connection():
    """Test that $connect Lambda stores connectionId in DynamoDB"""
    # Setup
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='test-connections',
        KeySchema=[{'AttributeName': 'connectionId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'connectionId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    os.environ['WEBSOCKET_CONNECTIONS_TABLE'] = 'test-connections'
    
    # Mock event
    event = {
        'requestContext': {'connectionId': 'test-conn-123'}
    }
    
    # Execute
    result = connect_handler(event, None)
    
    # Assert
    assert result['statusCode'] == 200
    
    # Verify stored in DynamoDB
    response = table.get_item(Key={'connectionId': 'test-conn-123'})
    assert 'Item' in response
    assert response['Item']['connectionId'] == 'test-conn-123'
    assert 'connected_at' in response['Item']
    assert 'ttl' in response['Item']


@mock_dynamodb
def test_websocket_connect_has_ttl():
    """Test that $connect Lambda sets TTL for auto-cleanup"""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='test-connections',
        KeySchema=[{'AttributeName': 'connectionId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'connectionId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    os.environ['WEBSOCKET_CONNECTIONS_TABLE'] = 'test-connections'
    
    current_time = int(time.time())
    event = {'requestContext': {'connectionId': 'conn-ttl-test'}}
    
    connect_handler(event, None)
    
    response = table.get_item(Key={'connectionId': 'conn-ttl-test'})
    item = response['Item']
    
    # TTL should be set to 24 hours from now
    expected_ttl = current_time + 86400
    assert item['ttl'] >= expected_ttl - 5  # Allow 5 second tolerance
    assert item['ttl'] <= expected_ttl + 5


@mock_dynamodb
def test_websocket_disconnect_removes_connection():
    """Test that $disconnect Lambda removes connectionId from DynamoDB"""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='test-connections',
        KeySchema=[{'AttributeName': 'connectionId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'connectionId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    os.environ['WEBSOCKET_CONNECTIONS_TABLE'] = 'test-connections'
    
    # First add a connection
    table.put_item(Item={'connectionId': 'conn-to-delete', 'connected_at': int(time.time()), 'ttl': int(time.time()) + 86400})
    
    # Verify it exists
    response = table.get_item(Key={'connectionId': 'conn-to-delete'})
    assert 'Item' in response
    
    # Disconnect
    event = {'requestContext': {'connectionId': 'conn-to-delete'}}
    result = disconnect_handler(event, None)
    
    # Assert
    assert result['statusCode'] == 200
    
    # Verify removed from DynamoDB
    response = table.get_item(Key={'connectionId': 'conn-to-delete'})
    assert 'Item' not in response


@mock_dynamodb
def test_websocket_disconnect_no_error_if_not_exists():
    """Test that $disconnect doesn't error if connectionId doesn't exist"""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    dynamodb.create_table(
        TableName='test-connections',
        KeySchema=[{'AttributeName': 'connectionId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'connectionId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    os.environ['WEBSOCKET_CONNECTIONS_TABLE'] = 'test-connections'
    
    # Try to disconnect non-existent connection
    event = {'requestContext': {'connectionId': 'never-existed'}}
    result = disconnect_handler(event, None)
    
    # Should still succeed (DynamoDB delete_item doesn't error on missing item)
    assert result['statusCode'] == 200


@mock_dynamodb
@patch('boto3.client')
def test_websocket_send_update_broadcasts_to_all(mock_boto_client):
    """Test that send_job_update broadcasts to all connected clients"""
    # Setup DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='test-connections',
        KeySchema=[{'AttributeName': 'connectionId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'connectionId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    os.environ['WEBSOCKET_CONNECTIONS_TABLE'] = 'test-connections'
    os.environ['WEBSOCKET_ENDPOINT'] = 'https://test.execute-api.us-east-1.amazonaws.com'
    
    # Add multiple connections
    connections = ['conn-1', 'conn-2', 'conn-3']
    for conn_id in connections:
        table.put_item(Item={
            'connectionId': conn_id,
            'connected_at': int(time.time()),
            'ttl': int(time.time()) + 86400
        })
    
    # Mock API Gateway Management API
    mock_apigw = MagicMock()
    mock_boto_client.return_value = mock_apigw
    mock_apigw.post_to_connection.return_value = {}
    
    # Event
    event = {
        'jobId': 'job-123',
        'status': 'PROCESSED',
        'results': {'output': 's3://bucket/path'}
    }
    
    # Execute
    result = send_update_handler(event, None)
    
    # Assert
    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    assert body['connections_notified'] == 3
    
    # Verify post_to_connection called for each connection
    assert mock_apigw.post_to_connection.call_count == 3
    
    # Verify message format
    calls = mock_apigw.post_to_connection.call_args_list
    for call in calls:
        assert 'ConnectionId' in call[1]
        assert 'Data' in call[1]
        data = json.loads(call[1]['Data'])
        assert data['type'] == 'job_update'
        assert data['jobId'] == 'job-123'
        assert data['status'] == 'PROCESSED'


@mock_dynamodb
@patch('boto3.client')
def test_websocket_send_update_cleans_gone_connections(mock_boto_client):
    """Test that send_job_update cleans up gone/stale connections"""
    # Setup DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='test-connections',
        KeySchema=[{'AttributeName': 'connectionId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'connectionId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    os.environ['WEBSOCKET_CONNECTIONS_TABLE'] = 'test-connections'
    os.environ['WEBSOCKET_ENDPOINT'] = 'https://test.execute-api.us-east-1.amazonaws.com'
    
    # Add connections
    table.put_item(Item={'connectionId': 'conn-alive', 'connected_at': int(time.time()), 'ttl': int(time.time()) + 86400})
    table.put_item(Item={'connectionId': 'conn-gone', 'connected_at': int(time.time()), 'ttl': int(time.time()) + 86400})
    
    # Mock API Gateway Management API
    mock_apigw = MagicMock()
    mock_boto_client.return_value = mock_apigw
    
    # First call succeeds, second raises GoneException
    def side_effect(**kwargs):
        if kwargs['ConnectionId'] == 'conn-gone':
            raise mock_apigw.exceptions.GoneException()
        return {}
    
    mock_apigw.post_to_connection.side_effect = side_effect
    mock_apigw.exceptions.GoneException = Exception
    
    event = {
        'jobId': 'job-456',
        'status': 'PROCESSED'
    }
    
    # Execute
    result = send_update_handler(event, None)
    
    # Assert
    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    assert body['connections_notified'] == 1
    assert body['cleaned_up'] == 1
    
    # Verify gone connection was deleted
    response = table.get_item(Key={'connectionId': 'conn-gone'})
    assert 'Item' not in response
    
    # Verify alive connection still exists
    response = table.get_item(Key={'connectionId': 'conn-alive'})
    assert 'Item' in response


@mock_dynamodb
def test_websocket_send_update_with_empty_connections():
    """Test send_job_update handles no connected clients"""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    dynamodb.create_table(
        TableName='test-connections',
        KeySchema=[{'AttributeName': 'connectionId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'connectionId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    os.environ['WEBSOCKET_CONNECTIONS_TABLE'] = 'test-connections'
    os.environ['WEBSOCKET_ENDPOINT'] = 'https://test.execute-api.us-east-1.amazonaws.com'
    
    event = {
        'jobId': 'job-789',
        'status': 'PROCESSED'
    }
    
    with patch('boto3.client'):
        result = send_update_handler(event, None)
    
    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    assert body['connections_notified'] == 0
    assert body['cleaned_up'] == 0


@mock_dynamodb
def test_websocket_send_update_message_format():
    """Test that send_job_update sends properly formatted messages"""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='test-connections',
        KeySchema=[{'AttributeName': 'connectionId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'connectionId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    os.environ['WEBSOCKET_CONNECTIONS_TABLE'] = 'test-connections'
    os.environ['WEBSOCKET_ENDPOINT'] = 'https://test.execute-api.us-east-1.amazonaws.com'
    
    table.put_item(Item={'connectionId': 'test-conn', 'connected_at': int(time.time()), 'ttl': int(time.time()) + 86400})
    
    mock_apigw = MagicMock()
    
    with patch('boto3.client', return_value=mock_apigw):
        event = {
            'jobId': 'job-msg-test',
            'status': 'PROCESSING',
            'results': None
        }
        
        send_update_handler(event, None)
    
    # Get the call and extract message
    call_args = mock_apigw.post_to_connection.call_args
    message = json.loads(call_args[1]['Data'])
    
    # Verify message structure
    assert message['type'] == 'job_update'
    assert message['jobId'] == 'job-msg-test'
    assert message['status'] == 'PROCESSING'
    assert 'timestamp' in message
    assert isinstance(message['timestamp'], int)
