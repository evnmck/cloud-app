import requests
import csv
import json
from pathlib import Path

# Get schedule
schedule_url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId=147&season=2025&startDate=2025-03-01&endDate=2025-10-01"
schedule_response = requests.get(schedule_url)
schedule_data = schedule_response.json()

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
        game_response = requests.get(game_url)
        game_data = game_response.json()
        
        # Save raw game data (entire JSON as a string column)
        all_games.append({
            'gameId': game_pk,
            'date': date_str,
            'rawData': json.dumps(game_data)
        })
        
        game_count += 1

# Write to CSV
output_file = Path(__file__).parent / "yankees_games.csv"
with open(output_file, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=['gameId', 'date', 'rawData'])
    writer.writeheader()
    writer.writerows(all_games)

print(f"Created {output_file} with raw game data from {game_count} games")