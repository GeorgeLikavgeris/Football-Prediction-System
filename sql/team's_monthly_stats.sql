-- Monthly Stats for a Team

SET @team_name='AS Roma';

SELECT season_year,t.team_name,DATE_FORMAT(md.match_datetime,'%Y-%m') AS year_and_month,
	   COUNT(*) AS total_matches,
       SUM(
			CASE
				WHEN md.home_team_id=t.team_id THEN md.home_goals_ft
                WHEN md.away_team_id=t.team_id THEN md.away_goals_ft
                ELSE 0
			END
		) AS goals_scored,
        SUM(
			CASE
				WHEN md.home_team_id=t.team_id THEN md.away_goals_ft
				WHEN md.away_team_id=t.team_id THEN md.home_goals_ft
				ELSE 0
		    END
		) AS goals_conceded,
        
        SUM(
			CASE
				WHEN (md.home_team_id=t.team_id AND md.home_goals_ft>md.away_goals_ft)
                OR (md.away_team_id=t.team_id AND md.away_goals_ft>md.home_goals_ft)
                THEN 1 ELSE 0
			END
		) AS wins,
        
        SUM(
			CASE 
				WHEN (md.home_team_id=t.team_id AND md.home_goals_ft<md.away_goals_ft)
				OR (md.away_team_id=t.team_id AND md.away_goals_ft<md.home_goals_ft)
				THEN 1 ELSE 0
			END
		) AS loses,
        
        SUM(
			CASE
				WHEN md.home_goals_ft=md.away_goals_ft
                THEN 1 ELSE 0
			END
		) AS draws,
        
        ROUND(AVG(
				  CASE
					WHEN md.home_team_id=t.team_id THEN md.home_goals_ft
                    WHEN md.away_team_id=t.team_id THEN md.away_goals_ft
				  END
		),2) AS avg_goals_scored,
        
        ROUND(AVG(
					CASE 
                       WHEN md.home_team_id=t.team_id THEN md.away_goals_ft
                       WHEN md.away_team_id=t.team_id THEN md.home_goals_ft
                    END
		),2) AS avg_goals_conceded
	
FROM matches_details md
JOIN teams t ON t.team_id=md.home_team_id OR t.team_id=md.away_team_id
JOIN seasons s ON s.season_id=md.season_id

WHERE t.team_name=@team_name
GROUP BY s.season_year,t.team_name,DATE_FORMAT(md.match_datetime, '%Y-%m')
ORDER BY s.season_year,year_and_month;