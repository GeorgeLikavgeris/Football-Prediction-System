-- Create view for each team's total goals per season

CREATE VIEW team_goals_per_season AS

SELECT *,
DENSE_RANK() OVER (
PARTITION BY season_year, league_name
ORDER BY total_goals DESC
) AS rank_in_league

FROM (

SELECT
s.season_year,
l.league_name,
t.team_name,
SUM(goals) AS total_goals

FROM (

SELECT season_id, home_team_id AS team_id, home_goals_ft AS goals
FROM matches_details

UNION ALL

SELECT season_id, away_team_id AS team_id, away_goals_ft AS goals
FROM matches_details

) g

JOIN seasons s ON g.season_id = s.season_id
JOIN leagues l ON s.league_id = l.league_id
JOIN teams t ON g.team_id = t.team_id

GROUP BY s.season_year, l.league_name, t.team_name

) AS goals_table;

-- Find the top 3 teams with the most goals per league and per year
SELECT *
FROM team_goals_per_season
WHERE rank_in_league<=3;
