CREATE OR REPLACE VIEW vw_team_last5_summary AS
SELECT
team_id,
team_name,
league_name,
season_year,

-- Form string
GROUP_CONCAT(result ORDER BY match_datetime DESC SEPARATOR ' ') AS form_last5,

-- Avg goals scored and conceded
AVG(goals_scored) AS avg_goals_scored_last5,
AVG(goals_conceded) AS avg_goals_conceded_last5,

-- Wins / Draws / Losses
SUM(CASE WHEN result = 'W' THEN 1 ELSE 0 END) AS wins_last5,
SUM(CASE WHEN result = 'D' THEN 1 ELSE 0 END) AS draws_last5,
SUM(CASE WHEN result = 'L' THEN 1 ELSE 0 END) AS losses_last5,

-- Total Points
SUM(
CASE
WHEN result = 'W' THEN 3
WHEN result = 'D' THEN 1
ELSE 0
END
) AS points_last5

FROM vw_last5_matches

GROUP BY
team_id,
team_name,
league_name,
season_year;