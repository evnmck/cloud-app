import requests
import csv
import json
import time
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure retry strategy for resilience
def create_session_with_retries(retries=3, backoff_factor=0.5):
    """Create requests session with automatic retry and exponential backoff"""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Create session with retry logic
session = create_session_with_retries()
REQUEST_TIMEOUT = 30  # seconds

# Get schedule
schedule_url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId=147&season=2025&startDate=2025-03-01&endDate=2025-10-01"
try:
    schedule_response = session.get(schedule_url, timeout=REQUEST_TIMEOUT)
    schedule_response.raise_for_status()
    schedule_data = schedule_response.json()
except requests.exceptions.RequestException as e:
    print(f"Error fetching schedule: {e}")
    exit(1)

print(f"Found {len(schedule_data['dates'])} dates")

game_count = 0
max_games = 5

all_games = []

for date_obj in schedule_data['dates']:
    if game_count >= max_games:
        break
    
    date_str = date_obj['date']
    for game in date_obj['games']:
        if game_count >= max_games:
            break
        
        game_pk = game['gamePk']
        print(f"Fetching game {game_pk}...")
        
        game_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
        try:
            game_response = session.get(game_url, timeout=REQUEST_TIMEOUT)
            game_response.raise_for_status()
            game_data = game_response.json()
            
            # Save raw game data (entire JSON as a string column)
            all_games.append({
                'gameId': game_pk,
                'date': date_str,
                'rawData': json.dumps(game_data)
            })
            
            game_count += 1
            print(f"  ✓ Game {game_pk} saved")
            
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Failed to fetch game {game_pk}: {e}")
            continue

# Write to CSV
output_file = Path(__file__).parent / "yankees_games.csv"
with open(output_file, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=['gameId', 'date', 'rawData'])
    writer.writeheader()
    writer.writerows(all_games)

print(f"Created {output_file} with raw game data from {game_count} games")