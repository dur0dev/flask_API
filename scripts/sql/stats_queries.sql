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
WITH team_best_stats AS (
    SELECT 
        g.id as game_id,
        g.game_date,
        ht.name as home_team,
        ht.code as home_team_short,
        g.home_team_id,
        g.home_score,
        at.code as away_team_short,
        at.name as away_team,
        g.away_team_id,
        g.away_score,
        
        -- Home team best players with stats
        (SELECT fp.player_name FROM nba.fact_player_game_stats fp 
         WHERE fp.game_id = g.id AND fp.team_id = g.home_team_id 
         ORDER BY fp.fantasy_points DESC LIMIT 1) as home_best_fantasy_pointer,
        (SELECT fp.fantasy_points FROM nba.fact_player_game_stats fp 
         WHERE fp.game_id = g.id AND fp.team_id = g.home_team_id 
         ORDER BY fp.fantasy_points DESC LIMIT 1) as home_best_fantasy_pointer_points,
        
        (SELECT fp.player_name FROM nba.fact_player_game_stats fp 
         WHERE fp.game_id = g.id AND fp.team_id = g.home_team_id 
         ORDER BY fp.points DESC LIMIT 1) as home_best_scorer,
        (SELECT fp.points FROM nba.fact_player_game_stats fp 
         WHERE fp.game_id = g.id AND fp.team_id = g.home_team_id 
         ORDER BY fp.points DESC LIMIT 1) as home_best_scorer_points,
        
        (SELECT fp.player_name FROM nba.fact_player_game_stats fp 
         WHERE fp.game_id = g.id AND fp.team_id = g.home_team_id 
         ORDER BY fp.total_rebounds DESC LIMIT 1) as home_best_rebounder,
        (SELECT fp.total_rebounds FROM nba.fact_player_game_stats fp 
         WHERE fp.game_id = g.id AND fp.team_id = g.home_team_id 
         ORDER BY fp.total_rebounds DESC LIMIT 1) as home_best_rebounder_rebounds,
         
        (SELECT fp.player_name FROM nba.fact_player_game_stats fp 
         WHERE fp.game_id = g.id AND fp.team_id = g.home_team_id 
         ORDER BY fp.assists DESC LIMIT 1) as home_best_assister,
        (SELECT fp.assists FROM nba.fact_player_game_stats fp 
         WHERE fp.game_id = g.id AND fp.team_id = g.home_team_id 
         ORDER BY fp.assists DESC LIMIT 1) as home_best_assister_assists,
        
        -- Away team best players with stats
        (SELECT fp.player_name FROM nba.fact_player_game_stats fp 
         WHERE fp.game_id = g.id AND fp.team_id = g.away_team_id 
         ORDER BY fp.fantasy_points DESC LIMIT 1) as away_best_fantasy_pointer,
        (SELECT fp.fantasy_points FROM nba.fact_player_game_stats fp 
         WHERE fp.game_id = g.id AND fp.team_id = g.away_team_id 
         ORDER BY fp.fantasy_points DESC LIMIT 1) as away_best_fantasy_pointer_points,

        (SELECT fp.player_name FROM nba.fact_player_game_stats fp 
         WHERE fp.game_id = g.id AND fp.team_id = g.away_team_id 
         ORDER BY fp.points DESC LIMIT 1) as away_best_scorer,
        (SELECT fp.points FROM nba.fact_player_game_stats fp 
         WHERE fp.game_id = g.id AND fp.team_id = g.away_team_id 
         ORDER BY fp.points DESC LIMIT 1) as away_best_scorer_points,
         
        (SELECT fp.player_name FROM nba.fact_player_game_stats fp 
         WHERE fp.game_id = g.id AND fp.team_id = g.away_team_id 
         ORDER BY fp.total_rebounds DESC LIMIT 1) as away_best_rebounder,
        (SELECT fp.total_rebounds FROM nba.fact_player_game_stats fp 
         WHERE fp.game_id = g.id AND fp.team_id = g.away_team_id 
         ORDER BY fp.total_rebounds DESC LIMIT 1) as away_best_rebounder_rebounds,
         
        (SELECT fp.player_name FROM nba.fact_player_game_stats fp 
         WHERE fp.game_id = g.id AND fp.team_id = g.away_team_id 
         ORDER BY fp.assists DESC LIMIT 1) as away_best_assister,
        (SELECT fp.assists FROM nba.fact_player_game_stats fp 
         WHERE fp.game_id = g.id AND fp.team_id = g.away_team_id 
         ORDER BY fp.assists DESC LIMIT 1) as away_best_assister_assists
        
    FROM nba.dim_games g
    JOIN nba.dim_teams ht ON g.home_team_id = ht.id
    JOIN nba.dim_teams at ON g.away_team_id = at.id
    WHERE g.game_date = :game_date
)
SELECT * FROM team_best_stats;

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

