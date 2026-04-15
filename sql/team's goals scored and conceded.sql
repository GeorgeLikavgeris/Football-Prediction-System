-- Create view with team's goals scored and conceded

CREATE OR REPLACE VIEW team_attack_defense_rank AS

SELECT
	season_year,
	league_name,
	team_name,
	goals_scored,
	goals_conceded,

	DENSE_RANK() OVER (
	PARTITION BY season_year, league_name
	ORDER BY goals_scored DESC
	) AS attack_rank,

	DENSE_RANK() OVER (
	PARTITION BY season_year, league_name
	ORDER BY goals_conceded ASC
	) AS defense_rank

FROM (

	SELECT
	s.season_year,
	l.league_name,
	t.team_name,
	SUM(g.goals_scored) AS goals_scored,
	SUM(g.goals_conceded) AS goals_conceded

	FROM (

	SELECT
	season_id,
	home_team_id AS team_id,
	home_goals_ft AS goals_scored,
	away_goals_ft AS goals_conceded
	FROM matches_details

	UNION ALL

	SELECT
	season_id,
	away_team_id AS team_id,
	away_goals_ft AS goals_scored,
	home_goals_ft AS goals_conceded
	FROM matches_details

) g

JOIN seasons s ON g.season_id = s.season_id
JOIN leagues l ON s.league_id = l.league_id
JOIN teams t ON g.team_id = t.team_id

GROUP BY
s.season_year,
l.league_name,
t.team_name

) AS stats;

-- Find the top 5 teams with the most goals scored
SELECT *
FROM team_attack_defense_rank
WHERE attack_rank<=5
ORDER BY attack_rank ASC;

-- Find the top 5 teams with the less goals conceded
SELECT *
FROM team_attack_defense_rank
WHERE defense_rank<=5
ORDER BY defense_rank ASC;