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

-- Add new tables for additional resume sections
CREATE TABLE IF NOT EXISTS experience (
    id SERIAL PRIMARY KEY,
    userid INTEGER REFERENCES users(id),
    resumeid INTEGER REFERENCES resume(resumeid),
    job_title VARCHAR(255),
    company VARCHAR(255),
    start_date VARCHAR(20),
    end_date VARCHAR(20),
    description TEXT
);

CREATE TABLE IF NOT EXISTS achievements (
    id SERIAL PRIMARY KEY,
    userid INTEGER REFERENCES users(id),
    resumeid INTEGER REFERENCES resume(resumeid),
    achievement TEXT
);

CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    userid INTEGER REFERENCES users(id),
    resumeid INTEGER REFERENCES resume(resumeid),
    course_name VARCHAR(255),
    institution VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS interests (
    id SERIAL PRIMARY KEY,
    userid INTEGER REFERENCES users(id),
    resumeid INTEGER REFERENCES resume(resumeid),
    interest VARCHAR(255)
);