CREATE OR REPLACE VIEW vw_last5_matches AS
SELECT *
FROM (
	SELECT
		mi.match_id,
        s.season_year,
        l.league_name,
        mi.matchday,
        mi.match_datetime,
        t.team_id,
        t.team_name,
        ht.team_name AS home_team,
        at.team_name AS away_team,
        
        CASE 
			WHEN t.team_id=mi.home_team_id THEN mi.home_goals_ft
            ELSE mi.away_goals_ft
		END AS goals_scored,
        
        CASE 
			WHEN t.team_id=mi.home_team_id THEN mi.away_goals_ft
            ELSE mi.home_goals_ft
		END AS goals_conceded,
        
        CASE 
			WHEN t.team_id = mi.home_team_id AND mi.home_goals_ft>mi.away_goals_ft THEN 'W'
            WHEN t.team_id = mi.away_team_id AND mi.away_goals_ft>mi.home_goals_ft THEN 'W'
            WHEN mi.home_goals_ft=mi.away_goals_ft THEN 'D'
            ELSE 'L'
		END AS result,
        
        ROW_NUMBER() OVER (
			PARTITION BY t.team_id
            ORDER BY mi.match_datetime DESC, mi.match_id DESC
		) AS match_rank
	
	FROM matches_info mi
    JOIN seasons_c s ON mi.season_id=s.season_id
    JOIN leagues_c l ON s.league_id=l.league_id
    JOIN teams_c ht ON mi.home_team_id=ht.team_id
    JOIN teams_c at ON mi.away_team_id=at.team_id
    JOIN teams_c t ON t.team_id IN (mi.home_team_id, mi.away_team_id)
) t
WHERE match_rank<=5;
