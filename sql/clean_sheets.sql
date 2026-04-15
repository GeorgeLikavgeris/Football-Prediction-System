-- Clean sheets
SELECT team_name,
	SUM(CASE WHEN goals_conceded = 0 THEN 1 ELSE 0 END) AS clean_sheets,
    COUNT(*) AS total_matches
FROM (
	SELECT 
		home_team AS team_name,
        away_goals AS goals_conceded
	FROM vw_season_matches
    
    UNION ALL
    
    SELECT 
		away_team AS team_name,
        home_goals AS goals_conceded
	FROM vw_season_matches
) t
GROUP BY team_name;