from flask import Blueprint, request, jsonify
from db import engine
import pandas as pd
from sqlalchemy import text
import logging
from utils.sql_loader import get_query
from utils.swagger_loader import swagger_doc

admin_api = Blueprint("admin_api", __name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@admin_api.route("/trade-tool", methods=["POST"])
@swagger_doc('trade_tool')
def trade_tool():
  # Get JSON data from request body
  data = request.get_json()
  player_name = data.get("player_name")
  old_team_name = data.get("old_team_name")
  new_team_name = data.get("new_team_name")

  query_team = get_query('get_team_id')
  logger.info(f"Getting teams id ...")
  old_team_id = int(pd.read_sql(text(query_team), engine, params={"name": old_team_name})['id'].iloc[0])
  new_team_id = int(pd.read_sql(text(query_team), engine, params={"name": new_team_name})['id'].iloc[0])

  logger.info(f"Getting player id ...")
  query_player = get_query('get_player_id')
  player_id = int(pd.read_sql(text(query_player), engine, params={"name": player_name, 'team_id': old_team_id})['id'].iloc[0])

  if player_id:
      logger.info(f"Updating player id and inserting market transaction ...")
      query_update = get_query('update_player_id')
      query_insert = get_query('insert_market_transaction')

      with engine.begin() as conn:
        update_result = conn.execute(text(query_update), {"new_team_id": new_team_id, "player_id": player_id})
        logger.info(f"Updated {update_result.rowcount} rows")
    
        insert_result = conn.execute(text(query_insert), {"player_id": player_id, "old_team_id": old_team_id, "new_team_id": new_team_id})
        logger.info(f"Inserted {insert_result.rowcount} rows into market_control")

      return jsonify({
          "msg": 'Updated done succesfully',
          "player_id": player_id,
          "player_name": player_name,
          "old_team_name":old_team_name,
          "old_team_id": old_team_id,
          "new_team_name":new_team_name,
          "new_team_id": new_team_id
      })
  
  else:
      logger.info(f"No player found for {player_name} in team {old_team_id}")
      return jsonify({
          "msg": 'No player found',
      })


  
        

