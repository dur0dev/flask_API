from flask import Blueprint, request, jsonify
from db import engine
import pandas as pd
from sqlalchemy import text
import logging
from datetime import datetime
from utils.sql_loader import get_query
from utils.swagger_loader import swagger_doc
from datetime import datetime, timedelta

stats_api = Blueprint("stats_api", __name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_game_id(game_id):
  try:
      return pd.read_sql(text(get_query('validate_game_id')), engine, params={"game_id": int(game_id)})['count'].iloc[0] > 0
  except Exception as e:
      logger.error(f"Error validating game_id {game_id}: {e}")
      return False

def validate_game_date(date_string, date_format="%Y-%m-%d"):
  try:
      datetime.strptime(date_string, date_format)
      return True
  except (ValueError, TypeError):
      return False

@stats_api.route("/by-game", methods=["POST"])
@swagger_doc('get_game_stats')
def get_game_stats():
  try:
    # Get JSON data from request body
    data = request.get_json()
    game_id = data.get("game_id")
    
    if validate_game_id(game_id):
      logger.info(f"✅Game exists✅")
      logger.info(f"Prepairing total info...")
      game_info_df = pd.read_sql(text(get_query('get_total_game_info')), engine, params={"game_id": int(game_id)})

      if game_info_df.empty:
        return jsonify({"Error": "Game not found"}), 404
      
      logger.info(f"Prepairing players info...")

      home_players_df = pd.read_sql(text(get_query('get_players_info')), engine, params={"game_id": int(game_id), "team_id": int(game_info_df['home_team_id'].iloc[0])})
      away_players_df = pd.read_sql(text(get_query('get_players_info')), engine, params={"game_id": int(game_id), "team_id": int(game_info_df['away_team_id'].iloc[0])})
      
      #DEBUG
      # home_players.to_json("home_df.json", orient="records", lines=True)
      # print("✅ JSON file saved: home_df.json")
      # away_players.to_json("away_df.json", orient="records", lines=True)
      # print("✅ JSON file saved: away_df.json")

      response_data = {
          "game_info": {
              "game_id": int(game_info_df['id'].iloc[0]),
              "date": str(game_info_df['game_date'].iloc[0]),
              "home_team": str(game_info_df['home_team'].iloc[0]),
              "home_team_id": str(game_info_df['home_team_id'].iloc[0]),
              "home_score": int(game_info_df['home_score'].iloc[0]),
              "away_team": str(game_info_df['away_team'].iloc[0]),
              "away_team_id": str(game_info_df['away_team_id'].iloc[0]),
              "away_score": int(game_info_df['away_score'].iloc[0]),
          },
          "home_players": home_players_df.to_dict('records'),
          "away_players": away_players_df.to_dict('records')
      }
    
      return jsonify(response_data)
    
    else:
      return jsonify({
            "success": False,
            "error": game_id
        }), 400

  except Exception as e:
      return jsonify({"error": str(e)}), 500
    
@stats_api.route("/by-date", methods=["POST"])
@swagger_doc('get_date_stats')
def get_date_stats():
  try:
    data = request.get_json()
    game_date = str(data.get("game_date"))

    if validate_game_date(game_date):
      logger.info(f"✅Date is correct✅: "+game_date)
      logger.info(f"Prepairing game info...")

      try:
        game_info_df = pd.read_sql(text(get_query('get_total_date_info')), engine, params={"game_date": game_date})
      except Exception as e:
        print(f"Error executing query: {e}")
        print(f"Query: {get_query('get_total_date_info')}")
        print(f"Params: {game_date}")

      if game_info_df.empty:
        return jsonify({"error": "No game for this date"}), 404
      
      # Convert all games to proper format
      games_list = []
      try:
        for _, row in game_info_df.iterrows():
          games_list.append({
              "game_id": int(row['game_id']),
              "date": row['game_date'].strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row['game_date']) else None,
              "home_team": str(row['home_team']),
              "home_team_short": str(row['home_team_short']),
              "home_team_id": str(row['home_team_id']),
              "home_score": int(row['home_score']),
              "home_best_fantasy_pointer": str(row['home_best_fantasy_pointer']),
              "home_best_fantasy_pointer_points": str(row['home_best_fantasy_pointer_points']),
              "home_best_scorer": str(row['home_best_scorer']),
              "home_best_scorer_points": int(row['home_best_scorer_points']),
              "home_best_rebounder": str(row['home_best_rebounder']),
              "home_best_rebounder_rebounds": int(row['home_best_rebounder_rebounds']),
              "home_best_assister": str(row['home_best_assister']),
              "home_best_assister_assists": int(row['home_best_assister_assists']),
              "away_team": str(row['away_team']),
              "away_team_short": str(row['away_team_short']),
              "away_team_id": str(row['away_team_id']),
              "away_score": int(row['away_score']),
              "away_best_fantasy_pointer": str(row['away_best_fantasy_pointer']),
              "away_best_fantasy_pointer_points": str(row['away_best_fantasy_pointer_points']),
              "away_best_scorer": str(row['away_best_scorer']),
              "away_best_scorer_points": int(row['away_best_scorer_points']),
              "away_best_rebounder": str(row['away_best_rebounder']),
              "away_best_rebounder_rebounds": int(row['away_best_rebounder_rebounds']),
              "away_best_assister": str(row['away_best_assister']),
              "away_best_assister_assists": int(row['away_best_assister_assists']),
          })
      except Exception as e:
        print(f"Error formatting df: {e}")

      response_data = {
        "games_count": len(games_list),
        "date": game_date,
        "games_info": games_list
      }

      return jsonify(response_data)
    else:
      return jsonify({
            "success": False,
            "error": game_date
      }), 400
       
  except Exception as e:
    return jsonify({"error": str(e)}), 500
