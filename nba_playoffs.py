import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from flask import Flask, jsonify

app = Flask(__name__)

class NBAPlayoffs:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.balldontlie.io/v1"
        self.headers = {
            "Authorization": api_key
        }

    def get_games(self, season=2024, cursor=None, per_page=100):
        """Get playoff games for the specified season with pagination"""
        params = {
            "seasons[]": season,
            "postseason": "true",
            "per_page": per_page
        }
        if cursor:
            params["cursor"] = cursor

        response = requests.get(
            f"{self.base_url}/games",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()

    def get_all_playoff_games(self, season=2024):
        """Get all playoff games for the specified season using pagination"""
        all_games = []
        cursor = None
        while True:
            response = self.get_games(season=season, cursor=cursor)
            games = response["data"]
            all_games.extend(games)
            if not response.get("meta", {}).get("next_cursor"):
                break
            cursor = response["meta"]["next_cursor"]
        return all_games

def get_nba_instance():
    # Load environment variables
    load_dotenv()

    # Get API key from environment variable
    api_key = os.getenv('BALLDONTLIE_API_KEY')
    if not api_key:
        raise ValueError("BALLDONTLIE_API_KEY not found in environment variables")

    return NBAPlayoffs(api_key)

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "message": "NBA Playoffs API is running"
    })

@app.route('/recent-games')
def get_recent_games():
    try:
        nba = get_nba_instance()
        games = nba.get_all_playoff_games(2024)

        # Filter for games in the last 7 days with scores (status == 'Final')
        today = datetime.utcnow()
        one_week_ago = today - timedelta(days=7)
        recent_final_games = []

        # Calculate series records for each matchup
        series_records = {}
        for game in games:
            if game["status"] == "Final":
                visitor_id = game["visitor_team"]["id"]
                home_id = game["home_team"]["id"]
                matchup_key = f"{min(visitor_id, home_id)}-{max(visitor_id, home_id)}"

                if matchup_key not in series_records:
                    series_records[matchup_key] = {"visitor_wins": 0, "home_wins": 0}

                if game["visitor_team_score"] > game["home_team_score"]:
                    series_records[matchup_key]["visitor_wins"] += 1
                else:
                    series_records[matchup_key]["home_wins"] += 1

        for game in games:
            date_str = game["date"]
            try:
                game_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                game_date = datetime.strptime(date_str, "%Y-%m-%d")
            if one_week_ago <= game_date <= today and game["status"] == "Final":
                # Add series record to the game data
                visitor_id = game["visitor_team"]["id"]
                home_id = game["home_team"]["id"]
                matchup_key = f"{min(visitor_id, home_id)}-{max(visitor_id, home_id)}"
                record = series_records[matchup_key]

                # Only include the properties we actually use in the templates
                optimized_game = {
                    "date": game["date"],
                    "visitor_team": {
                        "abbreviation": game["visitor_team"]["abbreviation"]
                    },
                    "visitor_team_score": game["visitor_team_score"],
                    "home_team": {
                        "abbreviation": game["home_team"]["abbreviation"]
                    },
                    "home_team_score": game["home_team_score"],
                    "series_record": {
                        "visitor_wins": record["visitor_wins"],
                        "home_wins": record["home_wins"]
                    }
                }
                recent_final_games.append(optimized_game)

        return jsonify(recent_final_games)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
