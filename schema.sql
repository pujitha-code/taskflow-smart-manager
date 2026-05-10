-- Smart Task Management System — Database Schema
-- Author: Allibad Pujitha
-- Run this in psql: psql -U postgres -d taskmanager -f schema.sql

-- Create database (run separately if needed)
-- CREATE DATABASE taskmanager;

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS users;

-- USERS TABLE
CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    username    VARCHAR(100) UNIQUE NOT NULL,
    email       VARCHAR(200) UNIQUE NOT NULL,
    password    VARCHAR(200) NOT NULL,         -- bcrypt hashed
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TASKS TABLE
CREATE TABLE tasks (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(200) NOT NULL,
    description TEXT,
    priority    VARCHAR(20) DEFAULT 'medium'
                CHECK (priority IN ('low', 'medium', 'high')),
    status      VARCHAR(20) DEFAULT 'pending'
                CHECK (status IN ('pending', 'in_progress', 'completed')),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INDEX for faster queries by user
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
