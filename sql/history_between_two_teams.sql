-- H2H Statistics (History between two teams)

SET @team1='SSC Napoli';
SET @team2='US Lecce';

SELECT 
	@team1 AS team_1,
    @team2 AS team_2,
	COUNT(*) AS total_matches,
    SUM(
		CASE
			WHEN (md.home_team_id=t1.team_id AND md.home_goals_ft>md.away_goals_ft)
				OR (md.away_team_id=t1.team_id AND md.away_goals_ft>md.home_goals_ft)
			THEN 1 ELSE 0
		END
	) AS team1_wins,
    
    SUM(
		CASE
			WHEN (md.home_team_id=t2.team_id AND md.home_goals_ft>md.away_goals_ft)
				OR (md.away_team_id=t2.team_id AND md.away_goals_ft>md.home_goals_ft)
			THEN 1 ELSE 0
		END
	) AS team2_wins,
    
    SUM(
		CASE
			WHEN md.home_goals_ft=md.away_goals_ft
            THEN 1 ELSE 0
		END
	) AS draws,
    
    SUM(
		CASE
			WHEN md.home_team_id=t1.team_id THEN md.home_goals_ft
            ELSE md.away_goals_ft
		END
	) AS team1_goals,
    
    SUM(
		CASE
			WHEN md.home_team_id=t2.team_id THEN md.home_goals_ft
            ELSE md.away_goals_ft
		END
	) AS team2_goals,
    
    ROUND(AVG(md.home_goals_ft+md.away_goals_ft),2) AS avg_goals_per_match,
    MAX(md.match_datetime) AS last_match_date

FROM matches_details md
JOIN teams t1 ON t1.team_name= @team1
JOIN teams t2 ON t2.team_name= @team2

WHERE (md.home_team_id=t1.team_id AND md.away_team_id=t2.team_id)
OR (md.home_team_id=t2.team_id AND md.away_team_id=t1.team_id);