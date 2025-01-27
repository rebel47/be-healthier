import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.express as px
import sqlite3
import hashlib
from data_manager import init_db, save_user_data, load_user_data, save_food_log, load_food_log, save_workout_log, load_workout_log, save_progress, load_progress
from utils import calculate_bmi, get_bmi_category, calculate_daily_calories
from nutrition_analyzer import NutritionAnalyzer, get_analysis_prompt

# Set page config FIRST
st.set_page_config(page_title="Health & Fitness Tracker", layout="wide")

# Initialize SQLite database for user credentials
user_credentials_db_path = "user_credentials.db"
user_conn = sqlite3.connect(user_credentials_db_path)
user_c = user_conn.cursor()
user_c.execute('''CREATE TABLE IF NOT EXISTS users
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT UNIQUE,
                   email TEXT,
                   name TEXT,
                   password TEXT)''')
user_conn.commit()

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize session state for authentication
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None

# Login widget (only show if not logged in)
if not st.session_state.get("authentication_status"):
    st.header("Login")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        # Fetch user credentials from the database
        user_c.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = user_c.fetchone()

        if result:
            hashed_password = result[0]
            # Verify the password
            if hash_password(password) == hashed_password:
                st.session_state["authentication_status"] = True
                st.session_state["username"] = username
                st.rerun()  # Refresh the page to update the UI
            else:
                st.error("Incorrect password")
        else:
            st.error("Username not found")

    # Registration widget (only show if not logged in)
    st.header("Register")
    register_username = st.text_input("Username", key="register_username")
    register_email = st.text_input("Email", key="register_email")
    register_name = st.text_input("Name", key="register_name")
    register_password = st.text_input("Password", type="password", key="register_password")
    register_confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")

    if st.button("Register"):
        if register_password != register_confirm_password:
            st.error("Passwords do not match!")
        else:
            try:
                # Hash the password
                hashed_password = hash_password(register_password)

                # Save the user to the database
                user_c.execute("INSERT INTO users (username, email, name, password) VALUES (?, ?, ?, ?)",
                             (register_username, register_email, register_name, hashed_password))
                user_conn.commit()
                st.success("User registered successfully! Please log in.")
            except sqlite3.IntegrityError:
                st.error("Username already exists. Please choose a different username.")

# Main application (only show if logged in)
elif st.session_state.get("authentication_status"):
    # User is authenticated
    st.write(f'Welcome *{st.session_state["username"]}*')

    # Logout button
    if st.button("Logout"):
        st.session_state["authentication_status"] = False
        st.session_state["username"] = None
        st.rerun()  # Refresh the page to update the UI

    # Initialize user-specific database
    init_db()

    # Navigation sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "User Profile", "Food Analyzer", "Exercise Tracker", "Progress Tracker"])

    # Show user stats in sidebar if profile exists
    user_data = load_user_data()
    if user_data:
        st.sidebar.subheader("Daily Targets")
        daily_calories = calculate_daily_calories(
            user_data['weight'], user_data['height'], user_data['age'],
            user_data['gender'], user_data['exercise_level'], user_data['goal']
        )
        
        # Get today's totals
        food_log = load_food_log(datetime.now().strftime("%Y-%m-%d"))
        workout_log = load_workout_log(datetime.now().strftime("%Y-%m-%d"))
        
        calories_consumed = food_log['calories'].sum() if not food_log.empty else 0
        calories_burned = workout_log['calories_burned'].sum() if not workout_log.empty else 0
        
        # Display metrics
        st.sidebar.metric("Calorie Target", f"{daily_calories}")
        st.sidebar.metric("Calories Consumed", f"{calories_consumed:.0f}")
        st.sidebar.metric("Calories Burned", f"{calories_burned:.0f}")
        st.sidebar.metric("Net Calories", f"{calories_consumed - calories_burned:.0f}")
        
        if not food_log.empty:
            st.sidebar.subheader("Today's Macros")
            st.sidebar.metric("Protein", f"{food_log['protein'].sum():.1f}g")
            st.sidebar.metric("Carbs", f"{food_log['carbs'].sum():.1f}g")
            st.sidebar.metric("Fat", f"{food_log['fat'].sum():.1f}g")

    # Page content
    if page == "Home":
        st.title("Health & Fitness Tracker")
        
        if not user_data:
            st.info("👋 Welcome! Please complete your profile to get started.")
        else:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("Profile Overview")
                bmi = calculate_bmi(user_data['weight'], user_data['height'])
                st.metric("BMI", f"{bmi:.1f} ({get_bmi_category(bmi)})")
                st.metric("Weight Goal", f"{user_data['target_weight']} kg")
                
            with col2:
                st.subheader("Today's Progress")
                st.metric("Calories", f"{calories_consumed}/{daily_calories}",
                         delta=float(daily_calories - calories_consumed))
                
            with col3:
                st.subheader("Exercise Log")
                st.metric("Calories Burned", f"{calories_burned}",
                         delta=float(calories_burned))

    elif page == "User Profile":
        st.header("User Profile")
        user_data = load_user_data()
        
        col1, col2 = st.columns(2)
        
        with col1:
            weight = st.number_input("Current Weight (kg)", 30.0, 200.0, 
                                   value=user_data.get('weight', 70.0) if user_data else 70.0)
            height = st.number_input("Height (cm)", 100.0, 250.0, 
                                   value=user_data.get('height', 170.0) if user_data else 170.0)
            age = st.number_input("Age", 15, 100, 
                                value=user_data.get('age', 30) if user_data else 30)
            gender = st.selectbox("Gender", ["Male", "Female"], 
                                index=0 if user_data and user_data.get('gender') == "Male" else 1)
        
        with col2:
            target_weight = st.number_input("Target Weight (kg)", 30.0, 200.0, 
                                          value=user_data.get('target_weight', 65.0) if user_data else 65.0)
            goal = st.selectbox("Goal", ["Weight Loss", "Maintenance", "Weight Gain"],
                              index=["Weight Loss", "Maintenance", "Weight Gain"].index(
                                  user_data.get('goal', 'Maintenance')) if user_data else 1)
            exercise_level = st.selectbox(
                "Activity Level",
                ["Sedentary", "Light", "Moderate", "Active", "Very Active"],
                index=["Sedentary", "Light", "Moderate", "Active", "Very Active"].index(
                    user_data.get('exercise_level', 'Moderate')) if user_data else 2)
            
        if st.button("Save Profile"):
            user_data = {
                "weight": weight,
                "height": height,
                "age": age,
                "gender": gender,
                "target_weight": target_weight,
                "goal": goal,
                "exercise_level": exercise_level,
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            }
            save_user_data(user_data)
            st.success("Profile updated successfully!")
            st.rerun()

    elif page == "Food Analyzer":
        st.header("Food Analyzer & Logger")
        st.info("Food analyzer functionality coming soon!")
        
    elif page == "Exercise Tracker":
        st.header("Exercise Tracker")
        st.info("Exercise tracker functionality coming soon!")
        
    elif page == "Progress Tracker":
        st.header("Progress Tracker")
        st.info("Progress tracker functionality coming soon!")

else:
    st.error("Please log in to access the application.")

# Close database connection
user_conn.close()
