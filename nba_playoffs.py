import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

class NBAPlayoffs:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.balldontlie.io/v1"
        self.headers = {
            "Authorization": api_key
        }

    def get_teams(self):
        """Get all NBA teams"""
        response = requests.get(f"{self.base_url}/teams", headers=self.headers)
        response.raise_for_status()
        return response.json()["data"]

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

    def get_team_standings(self, season=2024):
        """Get team standings for the specified season"""
        response = requests.get(
            f"{self.base_url}/standings",
            headers=self.headers,
            params={"season": season}
        )
        response.raise_for_status()
        return response.json()["data"]

    def get_all_games_for_month(self, year=2025, month=5):
        """Get all games for a specific month"""
        all_games = []
        cursor = None

        while True:
            response = self.get_games(cursor=cursor)
            games = response["data"]

            # Filter games for the specified month
            month_games = []
            for game in games:
                try:
                    game_date = datetime.strptime(game["date"], "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    game_date = datetime.strptime(game["date"], "%Y-%m-%d")
                if game_date.month == month:
                    month_games.append(game)

            all_games.extend(month_games)

            # Check if there are more pages
            if not response.get("meta", {}).get("next_cursor"):
                break
            cursor = response["meta"]["next_cursor"]

        return all_games

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

def main():
    # Load environment variables
    load_dotenv()

    # Get API key from environment variable
    api_key = os.getenv('BALLDONTLIE_API_KEY')
    if not api_key:
        print("Error: BALLDONTLIE_API_KEY not found in environment variables")
        print("Please create a .env file with your API key: BALLDONTLIE_API_KEY=your_api_key_here")
        return

    try:
        nba = NBAPlayoffs(api_key)

        # Get teams
        teams = nba.get_teams()

        # Get all playoff games for the current season
        games = nba.get_all_playoff_games(2024)

        # Filter for games in the last 7 days with scores (status == 'Final')
        today = datetime.utcnow()
        one_week_ago = today - timedelta(days=7)
        recent_final_games = []
        for game in games:
            date_str = game["date"]
            try:
                game_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                game_date = datetime.strptime(date_str, "%Y-%m-%d")
            if one_week_ago <= game_date <= today and game["status"] == "Final":
                recent_final_games.append((game, game_date))

        # Build win/loss records for each team vs each opponent
        win_loss = {}
        for game in games:
            if game["status"] != "Final":
                continue
            home_id = game["home_team"]["id"]
            visitor_id = game["visitor_team"]["id"]
            home_score = game["home_team_score"]
            visitor_score = game["visitor_team_score"]
            # Initialize dicts
            win_loss.setdefault(home_id, {}).setdefault(visitor_id, {"win": 0, "loss": 0})
            win_loss.setdefault(visitor_id, {}).setdefault(home_id, {"win": 0, "loss": 0})
            # Update win/loss
            if home_score > visitor_score:
                win_loss[home_id][visitor_id]["win"] += 1
                win_loss[visitor_id][home_id]["loss"] += 1
            else:
                win_loss[visitor_id][home_id]["win"] += 1
                win_loss[home_id][visitor_id]["loss"] += 1

        print(f"\nPlayoff Games with Scores in the Last Week:")
        print("-" * 50)
        for game, game_date in sorted(recent_final_games, key=lambda x: x[1]):
            home_team = next(team for team in teams if team["id"] == game["home_team"]["id"])
            visitor_team = next(team for team in teams if team["id"] == game["visitor_team"]["id"])
            date = game_date.strftime("%Y-%m-%d")
            home_id = home_team["id"]
            visitor_id = visitor_team["id"]
            # Get win/loss records
            home_vs_visitor = win_loss[home_id][visitor_id]
            visitor_vs_home = win_loss[visitor_id][home_id]
            print(f"{date}: {visitor_team['full_name']} ({visitor_vs_home['win']}-{visitor_vs_home['loss']}) @ {home_team['full_name']} ({home_vs_visitor['win']}-{home_vs_visitor['loss']})")
            print(f"Score: {game['visitor_team_score']}-{game['home_team_score']}")
            print()

    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
