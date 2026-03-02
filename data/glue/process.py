#!/usr/bin/env python3
"""
Glue job to process Yankees game data from MLB API
Extracts game summary, weather, player performance, and pitch-level details
"""

import json
import sys
import boto3
import pandas as pd
from datetime import datetime, timezone
import os

s3_client = boto3.client('s3')
dynamodb = boto3.resource("dynamodb")


def extract_game_summary(game_data):
    """Extract high-level game information"""
    live_data = game_data.get('liveData', {})
    game_data_obj = game_data.get('gameData', {})
    boxscore = live_data.get('boxscore', {})
    
    teams = game_data_obj.get('teams', {})
    home_team = teams.get('home', {})
    away_team = teams.get('away', {})
    
    home_stats = boxscore.get('teams', {}).get('home', {}).get('teamStats', {}).get('batting', {})
    away_stats = boxscore.get('teams', {}).get('away', {}).get('teamStats', {}).get('batting', {})
    
    return {
        'home_team': home_team.get('name'),
        'away_team': away_team.get('name'),
        'home_score': home_stats.get('runs', 0),
        'away_score': away_stats.get('runs', 0),
        'winner': home_team.get('name') if home_stats.get('runs', 0) > away_stats.get('runs', 0) else away_team.get('name'),
        'game_date': game_data_obj.get('dateTime', ''),
        'venue': game_data_obj.get('venue', {}).get('name', ''),
    }


def extract_weather(game_data):
    """Extract weather information"""
    weather = game_data.get('gameData', {}).get('weather', {})
    return {
        'temp': weather.get('temp'),
        'condition': weather.get('condition'),
        'wind_speed': weather.get('wind', {}).get('speed'),
        'wind_direction': weather.get('wind', {}).get('direction'),
    }


def extract_plays(game_data):
    """Extract play-by-play data with pitcher and batter info"""
    plays_list = game_data.get('liveData', {}).get('plays', {}).get('allPlays', [])
    
    processed_plays = []
    
    for play in plays_list:
        matchup = play.get('matchup', {})
        batter = matchup.get('batter', {})
        pitcher = matchup.get('pitcher', {})
        result = play.get('result', {})
        about = play.get('about', {})
        pitch_data = play.get('pitchData', {})
        count = play.get('count', {})
        
        processed_plays.append({
            'inning': about.get('inning'),
            'half_inning': about.get('halfInning'),  # "top" or "bottom"
            'batter_id': batter.get('id'),
            'batter_name': batter.get('fullName'),
            'batter_hand': matchup.get('batterHand'),  # L or R
            'pitcher_id': pitcher.get('id'),
            'pitcher_name': pitcher.get('fullName'),
            'pitcher_hand': matchup.get('pitcherHand'),  # L or R
            'pitch_type': pitch_data.get('pitchType'),  # e.g., "FF" (four-seam fastball)
            'pitch_velocity': pitch_data.get('startSpeed'),  # mph
            'balls': count.get('balls'),
            'strikes': count.get('strikes'),
            'outs': count.get('outs'),
            'event_type': result.get('eventType'),  # e.g., "single", "home_run", "strikeout"
            'event_description': result.get('description'),
            'home_run': result.get('homeRun', False),
            'rbi': result.get('rbi', 0),
            'is_hit': result.get('isHit', False),
        })
    
    return processed_plays


def extract_player_stats(game_data):
    """Extract individual player stats from boxscore"""
    boxscore = game_data.get('liveData', {}).get('boxscore', {})
    
    player_stats = []
    
    for team_side in ['home', 'away']:
        team = boxscore.get('teams', {}).get(team_side, {})
        team_name = game_data.get('gameData', {}).get('teams', {}).get(team_side, {}).get('name', '')
        
        for player_id, player_data in team.get('players', {}).items():
            person = player_data.get('person', {})
            stats = player_data.get('stats', {}).get('batting', {})
            position = player_data.get('position', {})
            
            player_stats.append({
                'team': team_name,
                'player_id': person.get('id'),
                'player_name': person.get('fullName'),
                'position': position.get('abbreviation'),
                'at_bats': stats.get('atBats', 0),
                'hits': stats.get('hits', 0),
                'runs': stats.get('runs', 0),
                'home_runs': stats.get('homeRuns', 0),
                'rbi': stats.get('rbi', 0),
                'strikeouts': stats.get('strikeOuts', 0),
                'walks': stats.get('baseOnBalls', 0),
                'batting_average': stats.get('avg'),
                'on_base_percentage': stats.get('obp'),
                'slugging_percentage': stats.get('slg'),
            })
    
    return player_stats


def process_game(raw_game_json, game_id, date):
    """Process a single game's data"""
    try:
        if isinstance(raw_game_json, str):
            game_data = json.loads(raw_game_json)
        else:
            game_data = raw_game_json
            
        # Ensure we got a dict
        if not isinstance(game_data, dict):
            print(f"Warning: game_data is {type(game_data)} for game {game_id}, skipping")
            return None
        
        # Recursively parse any nested JSON strings
        def parse_nested(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, str) and v.startswith('{'):
                        try:
                            obj[k] = json.loads(v)
                            parse_nested(obj[k])
                        except:
                            pass
                    elif isinstance(v, dict) or isinstance(v, list):
                        parse_nested(v)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict) or isinstance(item, list):
                        parse_nested(item)
        
        parse_nested(game_data)
            
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON for game {game_id}: {str(e)}")
        return None
    
    try:
        return {
            'game_id': game_id,
            'date': date,
            'summary': extract_game_summary(game_data),
            'weather': extract_weather(game_data),
            'plays': extract_plays(game_data),
            'player_stats': extract_player_stats(game_data),
        }
    except Exception as e:
        print(f"Error extracting data for game {game_id}: {str(e)}")
        print(f"game_data type: {type(game_data)}")
        print(f"game_data keys: {game_data.keys() if isinstance(game_data, dict) else 'N/A'}")
        import traceback
        traceback.print_exc()
        raise


def update_job_repository(job_id: str, status: str, **extra_fields):
    """Update job record in DynamoDB"""
    jobs_table = dynamodb.Table(os.environ["JOBS_TABLE_NAME"])
    
    update_expr = 'SET #status = :status, updatedAt = :now'
    attr_names = {'#status': 'status'}
    attr_values = {
        ':status': status,
        ':now': datetime.now(timezone.utc).isoformat(),
    }
    
    for i, (key, value) in enumerate(extra_fields.items()):
        update_expr += f', {key} = :val{i}'
        attr_values[f':val{i}'] = value
    
    jobs_table.update_item(
        Key={'jobId': job_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=attr_names,
        ExpressionAttributeValues=attr_values,
    )


def handler(event, context):
    """AWS Glue job handler"""
    print(f"Event: {event}")
    print(f"sys.argv full: {sys.argv}")
    print(f"Number of args: {len(sys.argv)}")
    
    # Get job parameters from Glue job arguments
    # These are passed by Step Function in the RUN_JOB integration
    job_id = event.get('jobId')
    bucket = event.get('bucket')
    key = event.get('key')
    
    print(f"From event - jobId: {job_id}, bucket: {bucket}, key: {key}")
    
    # Try parsing from sys.argv as fallback
    if not job_id and '--jobId' in sys.argv:
        idx = sys.argv.index('--jobId')
        if idx + 1 < len(sys.argv):
            job_id = sys.argv[idx + 1]
    if not bucket and '--bucket' in sys.argv:
        idx = sys.argv.index('--bucket')
        if idx + 1 < len(sys.argv):
            bucket = sys.argv[idx + 1]
    if not key and '--key' in sys.argv:
        idx = sys.argv.index('--key')
        if idx + 1 < len(sys.argv):
            key = sys.argv[idx + 1]
    
    print(f"Final extracted - jobId: {job_id}, bucket: {bucket}, key: {key}")
    
    # Validate we have all required parameters
    if not job_id or not bucket or not key:
        error_msg = f"Missing required parameters: jobId={job_id}, bucket={bucket}, key={key}"
        print(f"Error: {error_msg}")
        raise ValueError(error_msg)
    
    print(f"Processing s3://{bucket}/{key}")
    
    try:
        # Read CSV from S3 using pandas (handles large fields automatically)
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        csv_content = obj['Body'].read().decode('utf-8')
        
        # Read CSV with pandas
        df = pd.read_csv(pd.io.common.StringIO(csv_content))
        
        processed_games = []
        
        for _, row in df.iterrows():
            game_id = row['gameId']
            date = row['date']
            raw_data = row['rawData']
            
            print(f"Processing game {game_id}, rawData type: {type(raw_data)}, length: {len(str(raw_data)) if raw_data else 0}")
            
            if pd.notna(raw_data):  # Check if not NaN
                processed = process_game(raw_data, game_id, date)
                if processed:
                    processed_games.append(processed)
        
        # Save processed data back to S3
        output_key = f"processed/{job_id}/games_processed.json"
        s3_client.put_object(
            Bucket=bucket,
            Key=output_key,
            Body=json.dumps(processed_games, indent=2),
            ContentType='application/json'
        )
        
        print(f"Processed {len(processed_games)} games")
        print(f"Output saved to s3://{bucket}/{output_key}")
        
        update_job_repository(
            job_id,
            'PROCESSED',
            processedDataLocation=f"s3://{bucket}/{output_key}"
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Success',
                'games_processed': len(processed_games),
                'output_location': f"s3://{bucket}/{output_key}"
            })
        }
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        import traceback
        traceback.print_exc()
        # Raise the exception to make the Glue job fail
        raise


# Glue job entry point - invoke handler when script runs
if __name__ == '__main__':
    # Get parameters from sys.argv passed by Glue
    glue_args = {}
    for i, arg in enumerate(sys.argv):
        if arg.startswith('--'):
            key = arg[2:]
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--'):
                glue_args[key] = sys.argv[i + 1]
    
    result = handler(glue_args, None)
    print(f"Handler result: {result}")

