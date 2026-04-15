-- Create view for all the current season
CREATE OR REPLACE VIEW vw_season_matches AS 
SELECT
	mi.match_id,
    mi.match_datetime,
    mi.matchday,
    s.season_year,
    l.league_name,
    
    -- Home Team Info
    ht.team_id AS home_team_id,
    ht.team_name AS home_team,
    mi.home_goals_ft AS home_goals,
    mi.away_goals_ft AS away_goals,
    
    -- Away Team Info
    at.team_id AS away_team_id,
    at.team_name AS away_team,
    
    -- Result for home team
    CASE 
		WHEN mi.home_goals_ft>mi.away_goals_ft THEN 'W'
        WHEN mi.home_goals_ft=mi.away_goals_ft THEN 'D'
        ELSE 'L'
	END AS home_result,
    
    -- Result for away team
    CASE
		WHEN mi.away_goals_ft>mi.home_goals_ft THEN 'W'
        WHEN mi.away_goals_ft=mi.home_goals_ft THEN 'D'
        ELSE 'L'
	END AS away_result
FROM matches_info mi
JOIN seasons_c s ON mi.season_id=s.season_id
JOIN leagues_c l ON s.league_id=l.league_id
JOIN teams_c ht ON mi.home_team_id=ht.team_id
JOIN teams_c at ON mi.home_team_id=at.team_id
ORDER BY s.season_year,l.league_name,mi.matchday;
