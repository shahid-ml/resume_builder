-- Create new tables for enhanced resume builder
-- Only creating the missing tables

CREATE TABLE IF NOT EXISTS experience (
    id SERIAL PRIMARY KEY,
    userid INTEGER REFERENCES users(userid),
    resumeid INTEGER REFERENCES resume(resumeid),
    job_title VARCHAR(255),
    company VARCHAR(255),
    start_date VARCHAR(20),
    end_date VARCHAR(20),
    description TEXT
);

CREATE TABLE IF NOT EXISTS achievements (
    id SERIAL PRIMARY KEY,
    userid INTEGER REFERENCES users(userid),
    resumeid INTEGER REFERENCES resume(resumeid),
    achievement TEXT
);

CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    userid INTEGER REFERENCES users(userid),
    resumeid INTEGER REFERENCES resume(resumeid),
    course_name VARCHAR(255),
    institution VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS interests (
    id SERIAL PRIMARY KEY,
    userid INTEGER REFERENCES users(userid),
    resumeid INTEGER REFERENCES resume(resumeid),
    interest VARCHAR(255)
);