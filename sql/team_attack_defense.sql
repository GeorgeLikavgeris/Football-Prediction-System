-- Aggregated stats per team for Poisson model
CREATE OR REPLACE VIEW team_attack_defense AS
SELECT
	t.team_name,
	s.season_year,
	l.league_name,

	-- Home stats
	COUNT(CASE WHEN md.home_team_id = t.team_id THEN 1 END) AS home_matches,
	ROUND(AVG(CASE WHEN md.home_team_id = t.team_id THEN md.home_goals_ft END), 2) AS avg_home_goals_scored,
	ROUND(AVG(CASE WHEN md.home_team_id = t.team_id THEN md.away_goals_ft END), 2) AS avg_home_goals_conceded,

	-- Away stats
	COUNT(CASE WHEN md.away_team_id = t.team_id THEN 1 END) AS away_matches,
	ROUND(AVG(CASE WHEN md.away_team_id = t.team_id THEN md.away_goals_ft END), 2) AS avg_away_goals_scored,
	ROUND(AVG(CASE WHEN md.away_team_id = t.team_id THEN md.home_goals_ft END), 2) AS avg_away_goals_conceded

FROM matches_info md
JOIN teams_c t ON t.team_id = md.home_team_id OR t.team_id = md.away_team_id
JOIN seasons_c s ON s.season_id = md.season_id
JOIN leagues_c l ON l.league_id = s.league_id

GROUP BY t.team_name, s.season_year, l.league_name
ORDER BY l.league_name, s.season_year, t.team_name;

