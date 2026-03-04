import os
import sys
from pathlib import Path

# Add modules to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "modules"))

os.environ["JOBS_TABLE_NAME"] = "test-jobs-table"

import pytest
import json
import csv
import io
from unittest.mock import Mock, patch, MagicMock
from process import (
    extract_game_summary,
    extract_weather,
    extract_plays,
    extract_player_stats,
    process_game,
    handler,
)


# Sample mock game data
@pytest.fixture
def mock_game_data():
    """Mock MLB game data structure"""
    return {
        'gameData': {
            'dateTime': '2025-03-28T13:05:00Z',
            'venue': {
                'name': 'Yankee Stadium'
            },
            'teams': {
                'home': {'name': 'New York Yankees'},
                'away': {'name': 'Boston Red Sox'}
            },
            'weather': {
                'temp': '65',
                'condition': 'Partly Cloudy',
                'wind': {
                    'speed': '10',
                    'direction': 'NW'
                }
            }
        },
        'liveData': {
            'boxscore': {
                'teams': {
                    'home': {
                        'teamStats': {
                            'batting': {
                                'runs': 5
                            }
                        },
                        'players': {
                            'ID592450': {
                                'person': {
                                    'id': 592450,
                                    'fullName': 'Aaron Judge'
                                },
                                'position': {'abbreviation': 'RF'},
                                'stats': {
                                    'batting': {
                                        'atBats': 4,
                                        'hits': 2,
                                        'runs': 1,
                                        'homeRuns': 1,
                                        'rbi': 2,
                                        'strikeOuts': 0,
                                        'baseOnBalls': 1,
                                        'avg': '.500',
                                        'obp': '.600',
                                        'slg': '1.000'
                                    }
                                }
                            }
                        }
                    },
                    'away': {
                        'teamStats': {
                            'batting': {
                                'runs': 3
                            }
                        },
                        'players': {
                            'ID123456': {
                                'person': {
                                    'id': 123456,
                                    'fullName': 'Xander Bogaerts'
                                },
                                'position': {'abbreviation': 'SS'},
                                'stats': {
                                    'batting': {
                                        'atBats': 3,
                                        'hits': 1,
                                        'runs': 0,
                                        'homeRuns': 0,
                                        'rbi': 1,
                                        'strikeOuts': 1,
                                        'baseOnBalls': 0,
                                        'avg': '.333',
                                        'obp': '.333',
                                        'slg': '.333'
                                    }
                                }
                            }
                        }
                    }
                }
            },
            'plays': {
                'allPlays': [
                    {
                        'about': {
                            'inning': 1,
                            'halfInning': 'top'
                        },
                        'matchup': {
                            'batter': {'id': 592450, 'fullName': 'Aaron Judge'},
                            'pitcher': {'id': 543333, 'fullName': 'Nathan Eovaldi'},
                            'batterHand': 'R',
                            'pitcherHand': 'R'
                        },
                        'pitchData': {
                            'pitchType': 'FF',
                            'startSpeed': 96.5
                        },
                        'count': {
                            'balls': 1,
                            'strikes': 0,
                            'outs': 0
                        },
                        'result': {
                            'eventType': 'home_run',
                            'description': 'Aaron Judge homers (1) on a 1-0 count',
                            'homeRun': True,
                            'rbi': 1,
                            'isHit': True
                        }
                    }
                ]
            }
        }
    }


class TestExtractGameSummary:
    def test_extract_game_summary_success(self, mock_game_data):
        """Test successful game summary extraction"""
        summary = extract_game_summary(mock_game_data)
        
        assert summary['home_team'] == 'New York Yankees'
        assert summary['away_team'] == 'Boston Red Sox'
        assert summary['home_score'] == 5
        assert summary['away_score'] == 3
        assert summary['winner'] == 'New York Yankees'
        assert summary['venue'] == 'Yankee Stadium'

    def test_extract_game_summary_away_wins(self, mock_game_data):
        """Test when away team wins"""
        mock_game_data['liveData']['boxscore']['teams']['away']['teamStats']['batting']['runs'] = 8
        summary = extract_game_summary(mock_game_data)
        
        assert summary['away_score'] == 8
        assert summary['winner'] == 'Boston Red Sox'

    def test_extract_game_summary_missing_data(self):
        """Test with missing data"""
        empty_data = {'liveData': {}, 'gameData': {}}
        summary = extract_game_summary(empty_data)
        
        assert summary['home_team'] is None
        assert summary['home_score'] == 0


class TestExtractWeather:
    def test_extract_weather_success(self, mock_game_data):
        """Test successful weather extraction"""
        weather = extract_weather(mock_game_data)
        
        assert weather['temp'] == '65'
        assert weather['condition'] == 'Partly Cloudy'
        assert weather['wind_speed'] == '10'
        assert weather['wind_direction'] == 'NW'

    def test_extract_weather_missing_data(self):
        """Test with missing weather data"""
        empty_data = {'gameData': {}}
        weather = extract_weather(empty_data)
        
        assert weather['temp'] is None
        assert weather['condition'] is None


class TestExtractPlays:
    def test_extract_plays_success(self, mock_game_data):
        """Test successful plays extraction"""
        plays = extract_plays(mock_game_data)
        
        assert len(plays) == 1
        assert plays[0]['batter_name'] == 'Aaron Judge'
        assert plays[0]['pitcher_name'] == 'Nathan Eovaldi'
        assert plays[0]['pitch_type'] == 'FF'
        assert plays[0]['pitch_velocity'] == 96.5
        assert plays[0]['home_run'] is True
        assert plays[0]['event_type'] == 'home_run'

    def test_extract_plays_no_plays(self):
        """Test with no plays"""
        empty_data = {'liveData': {'plays': {}}}
        plays = extract_plays(empty_data)
        
        assert plays == []

    def test_extract_plays_multiple_plays(self, mock_game_data):
        """Test with multiple plays"""
        mock_game_data['liveData']['plays']['allPlays'].append({
            'about': {'inning': 1, 'halfInning': 'bottom'},
            'matchup': {
                'batter': {'id': 123456, 'fullName': 'Xander Bogaerts'},
                'pitcher': {'id': 543333, 'fullName': 'Gerrit Cole'},
                'batterHand': 'R',
                'pitcherHand': 'R'
            },
            'pitchData': {'pitchType': 'SL', 'startSpeed': 86.0},
            'count': {'balls': 0, 'strikes': 2, 'outs': 1},
            'result': {
                'eventType': 'strikeout',
                'description': 'Xander Bogaerts strikes out',
                'homeRun': False,
                'rbi': 0,
                'isHit': False
            }
        })
        
        plays = extract_plays(mock_game_data)
        assert len(plays) == 2


class TestExtractPlayerStats:
    def test_extract_player_stats_success(self, mock_game_data):
        """Test successful player stats extraction"""
        stats = extract_player_stats(mock_game_data)
        
        # Should have 2 players (1 home, 1 away)
        assert len(stats) == 2
        
        # Check home team player
        judge_stats = [s for s in stats if s['player_name'] == 'Aaron Judge'][0]
        assert judge_stats['team'] == 'New York Yankees'
        assert judge_stats['position'] == 'RF'
        assert judge_stats['home_runs'] == 1
        assert judge_stats['rbi'] == 2
        assert judge_stats['batting_average'] == '0.500'

    def test_extract_player_stats_no_players(self):
        """Test with no players"""
        empty_data = {'liveData': {'boxscore': {'teams': {}}}}
        stats = extract_player_stats(empty_data)
        
        assert stats == []


class TestProcessGame:
    def test_process_game_success(self, mock_game_data):
        """Test successful game processing"""
        game_json = json.dumps(mock_game_data)
        processed = process_game(game_json, 'game_123', '2025-03-28')
        
        assert processed['game_id'] == 'game_123'
        assert processed['date'] == '2025-03-28'
        assert 'summary' in processed
        assert 'weather' in processed
        assert 'plays' in processed
        assert 'player_stats' in processed
        
        # Verify nested data
        assert processed['summary']['home_team'] == 'New York Yankees'
        assert processed['weather']['temp'] == '65'
        assert len(processed['plays']) == 1
        assert len(processed['player_stats']) == 2

    def test_process_game_invalid_json(self):
        """Test with invalid JSON"""
        processed = process_game('invalid json', 'game_123', '2025-03-28')
        
        assert processed is None


class TestHandler:
    @patch('glue_utils.dynamodb')
    @patch('process.s3_client')
    def test_handler_success(self, mock_s3, mock_dynamodb, mock_game_data):
        """Test handler success"""
        # Setup mock S3 with properly formatted CSV
        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=['gameId', 'date', 'rawData'])
        writer.writeheader()
        writer.writerow({
            'gameId': '779051',
            'date': '2025-03-28',
            'rawData': json.dumps(mock_game_data)
        })
        csv_content = csv_buffer.getvalue()
        
        mock_s3.get_object.return_value = {
            'Body': Mock(read=Mock(return_value=csv_content.encode('utf-8')))
        }
        
        # Setup mock DynamoDB
        mock_table = MagicMock()
        mock_table.update_item.return_value = {}
        mock_dynamodb.Table.return_value = mock_table
        
        event = {
            'jobId': 'job_123',
            'bucket': 'test-bucket',
            'key': 'uploads/job_123/yankees_games.csv'
        }
        context = Mock()
        context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test'
        
        result = handler(event, context)
        
        assert result['statusCode'] == 200
        assert 'games_processed' in json.loads(result['body'])
        mock_s3.put_object.assert_called_once()
        mock_table.update_item.assert_called_once()

    @patch('glue_utils.dynamodb')
    @patch('process.s3_client')
    def test_handler_s3_error(self, mock_s3, mock_dynamodb):
        """Test handler with S3 error - should raise exception"""
        mock_s3.get_object.side_effect = Exception('S3 error')
        
        # Setup mock DynamoDB
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        event = {
            'jobId': 'job_123',
            'bucket': 'test-bucket',
            'key': 'uploads/job_123/yankees_games.csv'
        }
        context = Mock()
        context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test'
        
        # Should raise exception, not return error response
        with pytest.raises(Exception, match='S3 error'):
            handler(event, context)

    @patch('glue_utils.dynamodb')
    @patch('process.s3_client')
    def test_handler_empty_csv(self, mock_s3, mock_dynamodb):
        """Test handler with empty CSV"""
        csv_content = 'gameId,date,rawData\n'
        mock_s3.get_object.return_value = {
            'Body': Mock(read=Mock(return_value=csv_content.encode('utf-8')))
        }
        
        # Setup mock DynamoDB
        mock_table = MagicMock()
        mock_table.update_item.return_value = {}
        mock_dynamodb.Table.return_value = mock_table
        
        event = {
            'jobId': 'job_123',
            'bucket': 'test-bucket',
            'key': 'uploads/job_123/yankees_games.csv'
        }
        context = Mock()
        context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test'
        
        result = handler(event, context)
        
        assert result['statusCode'] == 200
        mock_table.update_item.assert_called_once()
        body = json.loads(result['body'])
        assert body['games_processed'] == 0


class TestIntegration:
    def test_full_game_processing_pipeline(self, mock_game_data):
        """Test full pipeline from raw JSON to processed output"""
        game_json = json.dumps(mock_game_data)
        
        # Process the game
        processed = process_game(game_json, '779051', '2025-03-28')
        
        # Verify all levels of extraction
        assert processed is not None
        
        # Summary level
        summary = processed['summary']
        assert summary['winner'] == 'New York Yankees'
        
        # Play level
        plays = processed['plays']
        assert len(plays) > 0
        assert plays[0]['home_run'] is True
        
        # Player level
        stats = processed['player_stats']
        assert len(stats) > 0
        judges = [p for p in stats if 'Judge' in p['player_name']]
        assert len(judges) > 0
        assert judges[0]['home_runs'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
