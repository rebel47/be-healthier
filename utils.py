def calculate_bmi(weight, height_cm):
    height_m = height_cm / 100
    return round(weight / (height_m * height_m), 2)

def get_bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"

def calculate_daily_calories(weight, height, age, gender, activity_level, goal):
    # Harris-Benedict equation
    if gender == "Male":
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    
    activity_multipliers = {
        "Sedentary": 1.2,
        "Light": 1.375,
        "Moderate": 1.55,
        "Active": 1.725,
        "Very Active": 1.9
    }
    
    maintenance_calories = bmr * activity_multipliers[activity_level]
    
    # Adjust based on goal
    if goal == "Weight Loss":
        return round(maintenance_calories - 500)  # 500 calorie deficit
    elif goal == "Weight Gain":
        return round(maintenance_calories + 500)  # 500 calorie surplus
    else:
        return round(maintenance_calories)