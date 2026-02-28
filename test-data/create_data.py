import requests
import csv

url = "https://statsapi.mlb.com/api/v1/teams/147/games?season=2025"
response = requests.get(url)
print(response.json())

games = response.json()
print(f"Number of games: {len(games.get('games', []))}")

# Extract relevant fields and save to CSV
with open("yankees_games.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["gameId", "date", "opponent", "score", "result"])
    for game in games.get("games", []):
        writer.writerow([
            game["gamePk"],
            game["gameDateTime"],
            game["teams"]["away"]["team"]["name"],
            f"{game['teams']['home']['score']}-{game['teams']['away']['score']}",
            game["status"]["detailedState"],
        ])

print("Done!")