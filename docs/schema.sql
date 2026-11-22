-- MySQL schema for the CITS Skill Gap Analyzer.
-- The Flask app creates this automatically; run it manually only if needed.

CREATE DATABASE IF NOT EXISTS cits_skill_gap
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE cits_skill_gap;

CREATE TABLE IF NOT EXISTS students (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  roll_no         VARCHAR(32)  NOT NULL UNIQUE,
  name            VARCHAR(120) NOT NULL,
  trade           VARCHAR(80)  NOT NULL DEFAULT 'Computer Software Application (CSA)',
  batch           VARCHAR(40)  NOT NULL DEFAULT '2026-27',
  email           VARCHAR(160) NULL,
  attendance      FLOAT        NOT NULL DEFAULT 0,
  theory_marks    FLOAT        NOT NULL DEFAULT 0,
  practical_marks FLOAT        NOT NULL DEFAULT 0,
  test_score      FLOAT        NOT NULL DEFAULT 0,
  project_score   FLOAT        NOT NULL DEFAULT 0,
  skills_json     TEXT         NOT NULL,
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_students_roll (roll_no)
) ENGINE = InnoDB;

-- Example row (skills stored as JSON text):
-- INSERT INTO students
--   (roll_no, name, attendance, theory_marks, practical_marks, test_score, project_score, skills_json)
-- VALUES
--   ('CITS26CSA001', 'Aarav Sharma', 92, 78, 85, 74, 88,
--    '{"Python": 72, "Java": 84, "MySQL": 78, "HTML/CSS": 80,
--      "JavaScript": 70, "C/C++": 65, "MS Office": 85, "Soft Skills": 80}');
