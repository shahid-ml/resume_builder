-- SQL commands to update the database schema for enhanced resume builder

-- Add columns to resume table
ALTER TABLE resume ADD COLUMN name VARCHAR(255);
ALTER TABLE resume ADD COLUMN email VARCHAR(255);
ALTER TABLE resume ADD COLUMN phone VARCHAR(50);
ALTER TABLE resume ADD COLUMN summary TEXT;

-- Add columns to education table
ALTER TABLE education ADD COLUMN start_year VARCHAR(10);
ALTER TABLE education ADD COLUMN end_year VARCHAR(10);

-- Note: Skills and projects tables remain the same, but we will insert multiple rows for multiple skills/projects