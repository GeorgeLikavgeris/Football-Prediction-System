-- =====================================
-- RESET DATABASE (DELETE OLD TABLES)
-- =====================================

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS matches_info;
DROP TABLE IF EXISTS seasons_c;
DROP TABLE IF EXISTS leagues_c;
DROP TABLE IF EXISTS teams_c;

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================
-- 1. TRANSFORM THE CSV TO RELATION SCHEMA WITH THE USE OF TABLES
-- =====================================

-- =====================================
-- 2. CREATE TEAMS TABLE
-- =====================================

CREATE TABLE teams_c (
team_id INT AUTO_INCREMENT PRIMARY KEY,
team_name VARCHAR(100) NOT NULL,
UNIQUE (team_name)
);


-- =====================================
-- 3. CREATE LEAGUES TABLE
-- =====================================

CREATE TABLE leagues_c (
league_id INT AUTO_INCREMENT PRIMARY KEY,
league_name VARCHAR(100) NOT NULL,
UNIQUE (league_name)
);


-- =====================================
-- 4. CREATE SEASONS TABLE
-- =====================================

CREATE TABLE seasons_c (
season_id INT AUTO_INCREMENT PRIMARY KEY,
season_year INT NOT NULL,
league_id INT NOT NULL,

UNIQUE (season_year, league_id),

FOREIGN KEY (league_id)
REFERENCES leagues_c(league_id)
ON DELETE CASCADE
);


-- =====================================
-- 5. CREATE MATCHES_INFO (NORMALIZED)
-- =====================================

CREATE TABLE matches_info (
match_id INT AUTO_INCREMENT PRIMARY KEY,

season_id INT NOT NULL,
match_datetime DATETIME NOT NULL,

home_team_id INT NOT NULL,
away_team_id INT NOT NULL,

home_goals_ht INT,
away_goals_ht INT,
home_goals_ft INT,
away_goals_ft INT,

matchday INT,
over_under_ht INT,
over_under_ft INT,

-- 🔥 CRITICAL (no duplicates)
UNIQUE (match_datetime, home_team_id, away_team_id),

FOREIGN KEY (season_id)
REFERENCES seasons_c(season_id)
ON DELETE CASCADE,

FOREIGN KEY (home_team_id)
REFERENCES teams_c(team_id)
ON DELETE CASCADE,

FOREIGN KEY (away_team_id)
REFERENCES teams_c(team_id)
ON DELETE CASCADE
);


-- =====================================
-- 6. CREATE MATCHES (FLAT TABLE)
-- =====================================

CREATE TABLE matches (
id INT AUTO_INCREMENT PRIMARY KEY,

date DATETIME,
matchday INT,

home_team VARCHAR(100),
away_team VARCHAR(100),

home_score_ht INT,
away_score_ht INT,
home_score_ft INT,
away_score_ft INT,

final_score VARCHAR(10),
final_result CHAR(1),

league VARCHAR(100),
season INT,

over_under_ht INT,
over_under_ft INT,

-- 🔥 CRITICAL (no duplicates)
UNIQUE (date, home_team, away_team, league)
);


-- =====================================
-- 7. OPTIONAL INDEXES (PERFORMANCE)
-- =====================================

CREATE INDEX idx_match_date ON matches(date);
CREATE INDEX idx_league ON matches(league);
CREATE INDEX idx_matchday ON matches(matchday);

CREATE INDEX idx_matchinfo_date ON matches_info(match_datetime);
CREATE INDEX idx_matchinfo_season ON matches_info(season_id);
