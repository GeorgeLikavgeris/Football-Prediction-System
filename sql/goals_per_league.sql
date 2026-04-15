-- Goal Per League per Year

SELECT l.league_name,s.season_year, SUM(md.home_goals_ht + md.away_goals_ht+md.home_goals_ft + md.away_goals_ft) AS total_goals
FROM matches_details AS md
JOIN seasons s ON md.season_id=s.season_id
JOIN leagues l ON s.league_id=l.league_id
GROUP BY l.league_name, s.season_year
ORDER BY l.league_name,s.season_year;