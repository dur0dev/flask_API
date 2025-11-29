-- name: validate_game_id
SELECT
    COUNT(*) as count
FROM
    nba.dim_games
WHERE
    id = :game_id

-- name: get_total_game_info
SELECT 
    g.id,
    g.game_date,
    ht.name as home_team,
    g.home_team_id,
    g.home_score,
    at.name as away_team,
    g.away_team_id,
    g.away_score
FROM nba.dim_games g
JOIN nba.dim_teams ht ON g.home_team_id = ht.id
JOIN nba.dim_teams at ON g.away_team_id = at.id
WHERE g.id = :game_id

-- name: get_total_date_info
SELECT
    *
FROM
    nba.games_with_best_performers
WHERE 
    DATE(game_date) = :game_date

-- name: get_players_info
SELECT
    player_id,
    player_name, 
    ROUND(minutes_played / 60.0) as minutes_played,
    points,
    field_goals_made,
    field_goals_attempted,
    three_pointers_made,
    three_pointers_attempted, 
    free_throws_made,
    free_throws_attempted,
    offensive_rebounds,
    defensive_rebounds,
    total_rebounds, 
    assists,
    steals,
    blocks,
    turnovers,
    personal_fouls,
    plus_minus,
    field_goal_percentage,
    three_point_percentage,
    free_throw_percentage
FROM 
    nba.fact_player_game_stats s
WHERE 
    game_id = :game_id
    AND team_id = :team_id

