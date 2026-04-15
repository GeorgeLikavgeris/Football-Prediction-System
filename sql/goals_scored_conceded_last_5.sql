-- Average goals scored/conceded the last 5 matches
SELECT 
	team_id,
    team_name,
    league_name,
    season_year,
    ROUND(AVG(goals_scored),2) AS avg_goals_scored_last5,
    ROUND(AVG(goals_conceded),2) AS avg_goals_conceded_last5
FROM vw_last5_matches
GROUP BY
	team_id,
    team_name,
    league_name,
    season_year;
    