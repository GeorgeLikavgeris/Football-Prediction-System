-- Check the results of the team and if the match was over and the average goals

SET @team_name="FC Barcelona";

SELECT 
	s.season_year,
    t.team_name,
    result,
    COUNT(*) AS matches,
    ROUND(AVG(total_goals),2) AS avg_goals,
    SUM(CASE WHEN total_goals>2 THEN 1 ELSE 0 END) AS over_matches,
    ROUND(SUM(CASE WHEN total_goals>2 THEN 1 ELSE 0 END) / COUNT(*)*100,2)
    AS over_percentage,
    SUM(CASE WHEN total_goals<=2 THEN 1 ELSE 0 END) AS under_matches,
    ROUND(SUM(CASE WHEN total_goals<=2 THEN 1 ELSE 0 END) / COUNT(*)*100,2)
    AS under_percentage
FROM (
	SELECT season_id,home_team_id AS team_id,
    CASE
		WHEN home_goals_ft>away_goals_ft THEN 'Win'
        WHEN home_goals_ft<away_goals_ft THEN 'Loss'
        ELSE 'Draw'
	END AS result,
    home_goals_ft+away_goals_ft AS total_goals
    FROM matches_details
    UNION ALL
    SELECT season_id,away_team_id AS team_id,
    CASE
		WHEN away_goals_ft>home_goals_ft THEN 'Win'
        WHEN away_goals_ft<home_goals_ft THEN 'Loss'
        ELSE 'Draw'
	END AS result,
    home_goals_ft+away_goals_ft AS total_goals
    FROM matches_details
) g

JOIN seasons s ON g.season_id = s.season_id
JOIN teams t ON g.team_id=t.team_id

WHERE t.team_name = @team_name

GROUP BY s.season_year,t.team_name,result

ORDER BY s.season_year, result;