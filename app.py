import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.express as px
import sqlite3
import hashlib  # For password hashing
from data_manager import init_db, save_user_data, load_user_data, save_food_log, load_food_log, save_workout_log, load_workout_log, save_progress, load_progress
from utils import calculate_bmi, get_bmi_category, calculate_daily_calories
from nutrition_analyzer import NutritionAnalyzer, get_analysis_prompt

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
if not st.session_state.get("authentication_status"):
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

# Close user credentials database connection
user_conn.close()

# Check authentication status
if st.session_state.get("authentication_status"):
    # User is authenticated
    st.write(f'Welcome *{st.session_state["username"]}*')

    # Logout button
    if st.button("Logout"):
        st.session_state["authentication_status"] = False
        st.session_state["username"] = None
        st.rerun()  # Refresh the page to update the UI

    # Initialize user-specific database
    init_db(st.session_state["username"])

    # Page Functions
    def home_page():
        st.title("Health & Fitness Tracker")
        user_data = load_user_data(st.session_state["username"])
        
        if not user_data:
            st.info("👋 Welcome! Please complete your profile to get started.")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Profile Overview")
            bmi = calculate_bmi(user_data['weight'], user_data['height'])
            st.metric("BMI", f"{bmi} ({get_bmi_category(bmi)})")
            st.metric("Weight Goal", f"{user_data['target_weight']} kg")
            
        with col2:
            st.subheader("Today's Progress")
            daily_calories = calculate_daily_calories(
                user_data['weight'], user_data['height'], user_data['age'],
                user_data['gender'], user_data['exercise_level'], user_data['goal']
            )
            food_log = load_food_log(st.session_state["username"], datetime.now().strftime("%Y-%m-%d"))
            calories_consumed = food_log['calories'].sum()
            st.metric("Calories", f"{calories_consumed}/{daily_calories}",
              delta=float(daily_calories - calories_consumed))  # Convert to float
            
        with col3:
            st.subheader("Exercise Log")
            workout_log = load_workout_log(st.session_state["username"], datetime.now().strftime("%Y-%m-%d"))
            calories_burned = workout_log['calories_burned'].sum()
            st.metric("Calories Burned", f"{calories_burned}", delta=float(calories_consumed - calories_burned))

    def profile_page():
        st.header("User Profile")
        user_data = load_user_data(st.session_state["username"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            weight = st.number_input("Current Weight (kg)", 30.0, 200.0, 
                                   value=user_data.get('weight', 70.0))
            height = st.number_input("Height (cm)", 100.0, 250.0, 
                                   value=user_data.get('height', 170.0))
            age = st.number_input("Age", 15, 100, value=user_data.get('age', 30))
            gender = st.selectbox("Gender", ["Male", "Female"], 
                                index=0 if user_data.get('gender') == "Male" else 1)
        
        with col2:
            target_weight = st.number_input("Target Weight (kg)", 30.0, 200.0, 
                                          value=user_data.get('target_weight', 65.0))
            goal = st.selectbox("Goal", ["Weight Loss", "Maintenance", "Weight Gain"],
                              index=["Weight Loss", "Maintenance", "Weight Gain"].index(
                                  user_data.get('goal', 'Maintenance')))
            exercise_level = st.selectbox(
                "Activity Level",
                ["Sedentary", "Light", "Moderate", "Active", "Very Active"],
                index=["Sedentary", "Light", "Moderate", "Active", "Very Active"].index(
                    user_data.get('exercise_level', 'Moderate'))
            )
            dietary_pref = st.selectbox(
                "Dietary Preference",
                ["Vegetarian", "Vegan", "Non-Vegetarian"],
                index=["Vegetarian", "Vegan", "Non-Vegetarian"].index(
                    user_data.get('dietary_pref', 'Vegetarian'))
            )
        
        # Define allergies options
        allergies_options = ["Dairy", "Nuts", "Gluten", "Shellfish", "Soy", "Eggs"]
        
        # Ensure default allergies are valid options
        default_allergies = user_data.get('allergies', [])
        default_allergies = [allergy for allergy in default_allergies if allergy in allergies_options]
        
        allergies = st.multiselect(
            "Allergies/Intolerances",
            options=allergies_options,
            default=default_allergies
        )
        
        if st.button("Save Profile"):
            user_data = {
                "weight": weight,
                "height": height,
                "age": age,
                "gender": gender,
                "target_weight": target_weight,
                "goal": goal,
                "exercise_level": exercise_level,
                "dietary_pref": dietary_pref,
                "allergies": allergies,
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            }
            save_user_data(st.session_state["username"], user_data)
            st.success("Profile updated successfully!")

    def food_analyzer_page():
        st.header("Food Analyzer & Logger")
        
        # Create tabs for different input methods
        tab1, tab2 = st.tabs(["📸 Food Image Analysis", "✍️ Manual Entry"])
        
        with tab1:
            st.subheader("Analyze Food Image")
            image_type = st.radio("What are you uploading?", ["Food Label", "Food Image"])
            uploaded_file = st.file_uploader(
                "Upload Image", 
                type=['png', 'jpg', 'jpeg'],
                help="Upload either a nutrition label or a photo of your food"
            )
            
            # Initialize session state for analysis result
            if "analysis_result" not in st.session_state:
                st.session_state.analysis_result = None
            
            if uploaded_file and st.button("Analyze"):
                with st.spinner("Analyzing image..."):
                    try:
                        analyzer = NutritionAnalyzer()
                        prompt = get_analysis_prompt(image_type)
                        processed_image = analyzer.preprocess_image(uploaded_file)
                        result = analyzer.extract_nutrition_info(processed_image, prompt)
                        
                        if result is None:
                            st.error("Analysis failed: No result returned")
                            return
                        
                        # Store the result in session state
                        st.session_state.analysis_result = {
                            "result": result,
                            "image_type": image_type,
                            "uploaded_file": uploaded_file
                        }
                        
                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")
            
            # Display analysis results if available
            if st.session_state.analysis_result:
                result = st.session_state.analysis_result["result"]
                image_type = st.session_state.analysis_result["image_type"]
                uploaded_file = st.session_state.analysis_result["uploaded_file"]
                
                st.subheader("Analysis Results")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
                
                with col2:
                    if image_type == "Food Label":
                        st.write("📊 Nutritional Information:")
                        st.write(f"🔸 Calories: {result['calories']} kcal")
                        st.write(f"🔸 Protein: {result.get('protein', 0)}g")
                        st.write(f"🔸 Carbs: {result.get('carbohydrates', 0)}g")
                        st.write(f"🔸 Fat: {result.get('fat', 0)}g")
                    else:
                        st.write("🍽️ Detected Food Items:")
                        for item in result['food_items']:
                            st.write(f"🔸 {item['name']}: {item['calories']} kcal")
                        st.write("📊 Total Nutritional Information:")
                        st.write(f"🔸 Total Calories: {result['total_calories']} kcal")
                        st.write(f"🔸 Total Protein: {result.get('total_protein', 0)}g")
                        st.write(f"🔸 Total Carbs: {result.get('total_carbs', 0)}g")
                        st.write(f"🔸 Total Fat: {result.get('total_fat', 0)}g")
                
                # Add to food log section
                st.subheader("Add to Food Log")
                col1, col2 = st.columns(2)
                with col1:
                    meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
                    food_name = st.text_input("Food Name", 
                                            value="Analyzed Food Item" if image_type == "Food Label" 
                                            else ", ".join([item['name'] for item in result.get('food_items', [])]))
                
                if st.button("Add to Food Log"):
                    if image_type == "Food Label":
                        total_calories = result['calories']
                        total_protein = result.get('protein', 0)
                        total_carbs = result.get('carbohydrates', 0)
                        total_fat = result.get('fat', 0)
                    else:
                        total_calories = result['total_calories']
                        total_protein = result.get('total_protein', 0)
                        total_carbs = result.get('total_carbs', 0)
                        total_fat = result.get('total_fat', 0)
                    
                    entry = {
                        'date': datetime.now().strftime("%Y-%m-%d"),
                        'meal_type': meal_type,
                        'food_item': food_name,
                        'calories': float(total_calories),
                        'protein': float(total_protein),
                        'carbs': float(total_carbs),
                        'fat': float(total_fat)
                    }
                    save_food_log(st.session_state["username"], entry)
                    st.success("✅ Food added to log successfully!")
                    # Clear the analysis result after adding to log
                    st.session_state.analysis_result = None
        
        with tab2:
            st.subheader("Manual Food Entry")
            col1, col2 = st.columns(2)
            with col1:
                meal_type = st.selectbox("Select Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"], key="manual_meal_type")
                food_name = st.text_input("Food Item Name", key="manual_food_name")
                calories = st.number_input("Calories", 0, 2000, key="manual_calories")
            with col2:
                protein = st.number_input("Protein (g)", 0.0, 200.0, key="manual_protein")
                carbs = st.number_input("Carbohydrates (g)", 0.0, 200.0, key="manual_carbs")
                fat = st.number_input("Fat (g)", 0.0, 200.0, key="manual_fat")
            
            if st.button("Add Food Item", key="manual_add_food"):
                entry = {
                    'date': datetime.now().strftime("%Y-%m-%d"),
                    'meal_type': meal_type,
                    'food_item': food_name,
                    'calories': float(calories),
                    'protein': float(protein),
                    'carbs': float(carbs),
                    'fat': float(fat)
                }
                save_food_log(st.session_state["username"], entry)
                st.success("✅ Food item added to log!")
        
        # Display today's food log
        st.subheader("Today's Food Log")
        food_log = load_food_log(st.session_state["username"], datetime.now().strftime("%Y-%m-%d"))
        if not food_log.empty:
            st.dataframe(food_log)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Calories", f"{food_log['calories'].sum():.0f} kcal")
            with col2:
                st.metric("Total Protein", f"{food_log['protein'].sum():.1f}g")
            with col3:
                st.metric("Total Carbs", f"{food_log['carbs'].sum():.1f}g")

    def exercise_page():
        st.header("Exercise Tracker")
        
        user_data = load_user_data(st.session_state["username"])
        if not user_data:
            st.warning("Please complete your profile first!")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Log Exercise")
            exercise_type = st.selectbox("Exercise Type", ["Cardio", "Strength", "Flexibility", "HIIT"])
            exercise = st.selectbox("Exercise", ["Running", "Cycling", "Swimming", "Push-ups", "Yoga", "Burpees"])
            duration = st.number_input("Duration (minutes)", 1, 180)
            
            calories_burned = duration * 7  # Example calculation (adjust based on exercise type)
            
            if st.button("Log Exercise"):
                entry = {
                    'date': datetime.now().strftime("%Y-%m-%d"),
                    'exercise_type': exercise_type,
                    'exercise': exercise,
                    'duration': duration,
                    'calories_burned': calories_burned
                }
                save_workout_log(st.session_state["username"], entry)
                st.success("Exercise logged successfully!")
        
        with col2:
            st.subheader("Today's Exercise Summary")
            workout_log = load_workout_log(st.session_state["username"], datetime.now().strftime("%Y-%m-%d"))
            if not workout_log.empty:
                st.dataframe(workout_log)
                st.metric("Total Calories Burned", f"{workout_log['calories_burned'].sum():.0f}")

    def progress_tracker_page():
        st.header("Progress Tracker")
        
        user_data = load_user_data(st.session_state["username"])
        if not user_data:
            st.warning("Please complete your profile first!")
            return
        
        # Weight tracking
        progress_df = load_progress(st.session_state["username"])
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Log Today's Weight")
            weight = st.number_input("Weight (kg)", 30.0, 200.0, user_data['weight'])
            if st.button("Log Weight"):
                entry = {
                    'date': datetime.now().strftime("%Y-%m-%d"),
                    'weight': weight,
                    'calories_consumed': 0,  # Placeholder
                    'exercise_minutes': 0    # Placeholder
                }
                save_progress(st.session_state["username"], entry)
                st.success("Weight logged successfully!")
        
        # Progress visualization
        if not progress_df.empty:
            st.subheader("Weight Progress")
            fig = px.line(progress_df, x='date', y='weight', 
                         title='Weight Over Time')
            st.plotly_chart(fig)
            
            # Calculate stats
            if len(progress_df) > 1:
                total_loss = progress_df['weight'].iloc[-1] - progress_df['weight'].iloc[0]
                st.metric("Total Weight Change", f"{total_loss:.1f} kg")

    def main():
        st.set_page_config(page_title="Health & Fitness Tracker", layout="wide")
        
        # Navigation
        pages = {
            "Home": home_page,
            "User Profile": profile_page,
            "Food Analyzer": food_analyzer_page,
            "Exercise Tracker": exercise_page,
            "Progress Tracker": progress_tracker_page
        }
        st.sidebar.title("Navigation")
        page = st.sidebar.radio("Go to", list(pages.keys()))
        
        # Show user stats in sidebar if profile exists
        user_data = load_user_data(st.session_state["username"])
        if user_data:
            st.sidebar.subheader("Daily Targets")
            daily_calories = calculate_daily_calories(
                user_data['weight'], user_data['height'], user_data['age'],
                user_data['gender'], user_data['exercise_level'], user_data['goal']
            )
            
            # Get today's totals
            food_log = load_food_log(st.session_state["username"], datetime.now().strftime("%Y-%m-%d"))
            workout_log = load_workout_log(st.session_state["username"], datetime.now().strftime("%Y-%m-%d"))
            
            calories_consumed = food_log['calories'].sum()
            calories_burned = workout_log['calories_burned'].sum()
            
            # Display metrics
            st.sidebar.metric("Calorie Target", f"{daily_calories}")
            st.sidebar.metric("Calories Consumed", f"{calories_consumed:.0f}")
            st.sidebar.metric("Calories Burned", f"{calories_burned:.0f}")
            st.sidebar.metric("Net Calories", 
                             f"{calories_consumed - calories_burned:.0f}")
            
            # Display macronutrient breakdown
            if not food_log.empty:
                st.sidebar.subheader("Today's Macros")
                st.sidebar.metric("Protein", f"{food_log['protein'].sum():.1f}g")
                st.sidebar.metric("Carbs", f"{food_log['carbs'].sum():.1f}g")
                st.sidebar.metric("Fat", f"{food_log['fat'].sum():.1f}g")
        
        # Render selected page
        pages[page]()

if __name__ == "__main__":
    main()
