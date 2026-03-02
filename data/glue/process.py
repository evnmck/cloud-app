#!/usr/bin/env python3
"""
Glue job to process Yankees game data from MLB API
Extracts game summary, weather, player performance, and pitch-level details
"""

import json
import sys
from io import StringIO
import boto3
import pandas as pd
from datetime import datetime, timezone
import os

s3_client = boto3.client('s3')
dynamodb = boto3.resource("dynamodb")


def extract_game_summary(game_data):
    """Extract high-level game information"""
    live_data = game_data.get('liveData', {}) if isinstance(game_data.get('liveData'), dict) else {}
    game_data_obj = game_data.get('gameData', {}) if isinstance(game_data.get('gameData'), dict) else {}
    boxscore = live_data.get('boxscore', {}) if isinstance(live_data.get('boxscore'), dict) else {}
    
    teams = game_data_obj.get('teams', {}) if isinstance(game_data_obj.get('teams'), dict) else {}
    home_team = teams.get('home', {}) if isinstance(teams.get('home'), dict) else {}
    away_team = teams.get('away', {}) if isinstance(teams.get('away'), dict) else {}
    
    box_teams = boxscore.get('teams', {}) if isinstance(boxscore.get('teams'), dict) else {}
    home_box = box_teams.get('home', {}) if isinstance(box_teams.get('home'), dict) else {}
    away_box = box_teams.get('away', {}) if isinstance(box_teams.get('away'), dict) else {}
    home_team_stats = home_box.get('teamStats', {}) if isinstance(home_box.get('teamStats'), dict) else {}
    away_team_stats = away_box.get('teamStats', {}) if isinstance(away_box.get('teamStats'), dict) else {}
    home_stats = home_team_stats.get('batting', {}) if isinstance(home_team_stats.get('batting'), dict) else {}
    away_stats = away_team_stats.get('batting', {}) if isinstance(away_team_stats.get('batting'), dict) else {}
    
    home_score = home_stats.get('runs', 0)
    away_score = away_stats.get('runs', 0)
    
    venue = game_data_obj.get('venue', {}) if isinstance(game_data_obj.get('venue'), dict) else {}
    
    return {
        'home_team': home_team.get('name'),
        'away_team': away_team.get('name'),
        'home_score': home_score,
        'away_score': away_score,
        'winner': home_team.get('name') if home_score > away_score else away_team.get('name'),
        'game_date': game_data_obj.get('dateTime', ''),
        'venue': venue.get('name', ''),
    }


def extract_weather(game_data):
    """Extract weather information"""
    game_data_obj = game_data.get('gameData', {}) if isinstance(game_data.get('gameData'), dict) else {}
    weather = game_data_obj.get('weather', {}) if isinstance(game_data_obj.get('weather'), dict) else {}
    wind = weather.get('wind', {}) if isinstance(weather.get('wind'), dict) else {}
    
    return {
        'temp': weather.get('temp'),
        'condition': weather.get('condition'),
        'wind_speed': wind.get('speed'),
        'wind_direction': wind.get('direction'),
    }


def extract_plays(game_data):
    """Extract play-by-play data with pitcher and batter info"""
    live_data = game_data.get('liveData') or {}
    if not isinstance(live_data, dict):
        return []
    plays_dict = live_data.get('plays') or {}
    if not isinstance(plays_dict, dict):
        return []
    plays_list = plays_dict.get('allPlays', [])
    if not isinstance(plays_list, list):
        return []
    
    processed_plays = []
    
    for play in plays_list:
        if not isinstance(play, dict):
            continue
        matchup = play.get('matchup', {}) if isinstance(play.get('matchup'), dict) else {}
        batter = matchup.get('batter', {}) if isinstance(matchup.get('batter'), dict) else {}
        pitcher = matchup.get('pitcher', {}) if isinstance(matchup.get('pitcher'), dict) else {}
        result = play.get('result', {}) if isinstance(play.get('result'), dict) else {}
        about = play.get('about', {}) if isinstance(play.get('about'), dict) else {}
        pitch_data = play.get('pitchData', {}) if isinstance(play.get('pitchData'), dict) else {}
        count = play.get('count', {}) if isinstance(play.get('count'), dict) else {}
        
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
    if not isinstance(boxscore, dict):
        return []
    
    player_stats = []
    
    for team_side in ['home', 'away']:
        team = boxscore.get('teams', {}) if isinstance(boxscore.get('teams'), dict) else {}
        team = team.get(team_side, {}) if isinstance(team.get(team_side), dict) else {}
        
        game_data_obj_inner = game_data.get('gameData') or {}
        if isinstance(game_data_obj_inner, dict):
            teams_inner = game_data_obj_inner.get('teams') or {}
            team_side_obj = teams_inner.get(team_side) or {} if isinstance(teams_inner, dict) else {}
            team_name = team_side_obj.get('name', '') if isinstance(team_side_obj, dict) else ''
        else:
            team_name = ''
        
        players_dict = team.get('players') or {}
        players_items = players_dict.items() if isinstance(players_dict, dict) else []
        
        for player_id, player_data in players_items:
            if not isinstance(player_data, dict):
                continue
            person = player_data.get('person', {}) if isinstance(player_data.get('person'), dict) else {}
            stats = player_data.get('stats', {}) if isinstance(player_data.get('stats'), dict) else {}
            stats = stats.get('batting', {}) if isinstance(stats.get('batting'), dict) else {}
            position = player_data.get('position', {}) if isinstance(player_data.get('position'), dict) else {}
            
            # Extract raw stats
            at_bats = stats.get('atBats', 0)
            hits = stats.get('hits', 0)
            walks = stats.get('baseOnBalls', 0)
            home_runs = stats.get('homeRuns', 0)
            doubles = stats.get('doubles', 0)
            triples = stats.get('triples', 0)
            
            # Skip players with no activity
            if at_bats == 0 and hits == 0 and walks == 0:
                continue
            
            # Calculate batting average (hits / at_bats)
            batting_avg = f"{hits / at_bats:.3f}" if at_bats > 0 else "0.000"
            
            # Calculate on-base percentage: (H + BB) / (AB + BB + SF)
            # Assuming no SF (sacrifice flies) in data, simplified to (H + BB) / (AB + BB)
            obp = f"{(hits + walks) / (at_bats + walks):.3f}" if (at_bats + walks) > 0 else "0.000"
            
            # Calculate slugging percentage: total bases / at_bats
            total_bases = hits - doubles - triples - home_runs + (2 * doubles) + (3 * triples) + (4 * home_runs)
            slg = f"{total_bases / at_bats:.3f}" if at_bats > 0 else "0.000"
            
            player_stats.append({
                'team': team_name,
                'player_id': person.get('id'),
                'player_name': person.get('fullName'),
                'position': position.get('abbreviation'),
                'at_bats': at_bats,
                'hits': hits,
                'runs': stats.get('runs', 0),
                'home_runs': home_runs,
                'rbi': stats.get('rbi', 0),
                'strikeouts': stats.get('strikeOuts', 0),
                'walks': walks,
                'batting_average': batting_avg,
                'on_base_percentage': obp,
                'slugging_percentage': slg,
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
                        except (json.JSONDecodeError, TypeError) as e:
                            print(f"Warning: failed to parse nested JSON for key '{k}' in game {game_id}: {e}")
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
    
    # Set JOBS_TABLE_NAME from event if not already in environment
    if 'JOBS_TABLE_NAME' in event and 'JOBS_TABLE_NAME' not in os.environ:
        os.environ['JOBS_TABLE_NAME'] = event['JOBS_TABLE_NAME']
    
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
        df = pd.read_csv(StringIO(csv_content))
        
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

