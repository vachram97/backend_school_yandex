CREATE DATABASE citizens;
USE citizens;

CREATE TABLE imports (
    id INT NOT NULL
);
INSERT INTO imports VALUES (1);

CREATE TABLE import (
    import_id INT NOT NULL,
    citizen_id INT NOT NULL,
    town VARCHAR(100) NOT NULL,
    street VARCHAR(100) NOT NULL,
    building VARCHAR(100) NOT NULL,
    apartment INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    gender ENUM('male', 'female') NOT NULL,
    relatives TEXT NOT NULL,
    CONSTRAINT import_citizen_id PRIMARY KEY (import_id, citizen_id)
) CHARACTER SET utf8;

CREATE USER 'citizen_app'@'localhost' IDENTIFIED BY 'pass';
GRANT ALL PRIVILEGES ON citizens.* TO 'citizen_app'@'localhost';

