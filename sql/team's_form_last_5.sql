-- Form from a team the last 5 matches
SELECT 
	team_id,
    team_name,
    league_name,
    season_year,
    GROUP_CONCAT(result ORDER BY match_rank DESC SEPARATOR ' ') AS form_last5
FROM vw_last5_matches
GROUP BY
	team_id,
    team_name,
    league_name,
    season_year;

