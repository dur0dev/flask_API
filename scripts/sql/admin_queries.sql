-- name: get_team_id
SELECT
    id
FROM
    nba.dim_teams
WHERE
    name ILIKE '%' || :name || '%'

-- name: get_player_id
SELECT
    id
FROM
    nba.dim_players
WHERE
    name ILIKE '%' || :name || '%'
    and team_id = :team_id

-- name: update_player_id
UPDATE 
    nba.dim_players 
SET 
    team_id = :new_team_id
WHERE
    id = :player_id

-- name: insert_market_transaction
INSERT INTO 
    nba.fact_market (player_id, old_team_id, new_team_id, operation_date)
VALUES 
    (:player_id, :old_team_id, :new_team_id, CURRENT_DATE)