-- Average Goals per Result
SELECT
	team_name,
	venue,
	result,

	ROUND(AVG(goals_scored),2) AS avg_goals_scored,
	ROUND(AVG(goals_conceded),2) AS avg_goals_conceded,
	COUNT(*) AS matches

FROM (
	-- HOME
	SELECT
		home_team AS team_name,
		'HOME' AS venue,
		home_result AS result,
		home_goals AS goals_scored,
		away_goals AS goals_conceded
	FROM vw_season_matches

	UNION ALL

	-- AWAY
	SELECT
	away_team AS team_name,
	'AWAY' AS venue,
	away_result AS result,
	away_goals AS goals_scored,
	home_goals AS goals_conceded
	FROM vw_season_matches
) t

GROUP BY
	team_name,
	venue,
	result

ORDER BY
	team_name,
	venue,
	result;