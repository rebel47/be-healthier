import sqlite3
import pandas as pd
from datetime import datetime

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('data/health_tracker.db')
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            weight REAL,
            height REAL,
            age INTEGER,
            gender TEXT,
            target_weight REAL,
            goal TEXT,
            exercise_level TEXT,
            dietary_pref TEXT,
            allergies TEXT,
            last_updated TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS food_log (
            id INTEGER PRIMARY KEY,
            date TEXT,
            meal_type TEXT,
            food_item TEXT,
            calories REAL,
            protein REAL,
            carbs REAL,
            fat REAL
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS workout_log (
            id INTEGER PRIMARY KEY,
            date TEXT,
            exercise_type TEXT,
            exercise TEXT,
            duration INTEGER,
            calories_burned REAL
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY,
            date TEXT,
            weight REAL,
            calories_consumed REAL,
            exercise_minutes INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()

# Save user data
def save_user_data(user_data):
    conn = sqlite3.connect('data/health_tracker.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO users (weight, height, age, gender, target_weight, goal, exercise_level, dietary_pref, allergies, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_data['weight'], user_data['height'], user_data['age'], user_data['gender'],
        user_data['target_weight'], user_data['goal'], user_data['exercise_level'],
        user_data['dietary_pref'], ','.join(user_data['allergies']), user_data['last_updated']
    ))
    conn.commit()
    conn.close()

# Load user data
def load_user_data():
    conn = sqlite3.connect('data/health_tracker.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users ORDER BY id DESC LIMIT 1')
    user_data = c.fetchone()
    conn.close()
    
    if user_data:
        return {
            "weight": user_data[1],
            "height": user_data[2],
            "age": user_data[3],
            "gender": user_data[4],
            "target_weight": user_data[5],
            "goal": user_data[6],
            "exercise_level": user_data[7],
            "dietary_pref": user_data[8],
            "allergies": user_data[9].split(','),
            "last_updated": user_data[10]
        }
    return {}

# Save food log
def save_food_log(entry):
    conn = sqlite3.connect('data/health_tracker.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO food_log (date, meal_type, food_item, calories, protein, carbs, fat)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        entry['date'], entry['meal_type'], entry['food_item'],
        entry['calories'], entry['protein'], entry['carbs'], entry['fat']
    ))
    conn.commit()
    conn.close()

# Load food log
def load_food_log(date=None):
    conn = sqlite3.connect('data/health_tracker.db')
    query = 'SELECT * FROM food_log'
    if date:
        query += f" WHERE date = '{date}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Save workout log
def save_workout_log(entry):
    conn = sqlite3.connect('data/health_tracker.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO workout_log (date, exercise_type, exercise, duration, calories_burned)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        entry['date'], entry['exercise_type'], entry['exercise'],
        entry['duration'], entry['calories_burned']
    ))
    conn.commit()
    conn.close()

# Load workout log
def load_workout_log(date=None):
    conn = sqlite3.connect('data/health_tracker.db')
    query = 'SELECT * FROM workout_log'
    if date:
        query += f" WHERE date = '{date}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Save progress
def save_progress(entry):
    conn = sqlite3.connect('data/health_tracker.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO progress (date, weight, calories_consumed, exercise_minutes)
        VALUES (?, ?, ?, ?)
    ''', (
        entry['date'], entry['weight'], entry['calories_consumed'], entry['exercise_minutes']
    ))
    conn.commit()
    conn.close()

# Load progress
def load_progress():
    conn = sqlite3.connect('data/health_tracker.db')
    df = pd.read_sql_query('SELECT * FROM progress', conn)
    conn.close()
    return df