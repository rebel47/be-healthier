import google.generativeai as genai
from PIL import Image
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()  # Ensure this is called to load the .env file
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in a .env file or as an environment variable.")

# Configure the Gemini API
genai.configure(api_key=GOOGLE_API_KEY)

class NutritionAnalyzer:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.thresholds = {
            "calories": 300,
            "sugar": 25,
            "saturated_fat": 5,
            "sodium": 600,
            "protein": 5
        }
    
    def preprocess_image(self, image_file):
        try:
            image = Image.open(image_file)
            # Convert to RGB if necessary
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            # Resize if too large
            max_size = 1024
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            return image
        except Exception as e:
            raise ValueError(f"Error processing image: {str(e)}")

    def extract_nutrition_info(self, image, prompt):
        try:
            response = self.model.generate_content([image, prompt])
            
            # Log the raw response text
            print("Raw response from Gemini:", response.text)
            
            if not response.text.strip():
                raise ValueError("Empty response received from the model")
            
            # Extract JSON from response
            json_str = response.text.strip('`').strip()
            if json_str.startswith('json'):
                json_str = json_str[4:]
            
            # Handle extra data by finding the first valid JSON object
            try:
                # Find the first occurrence of '{' and the last occurrence of '}'
                start = json_str.find('{')
                end = json_str.rfind('}') + 1
                json_str = json_str[start:end]
                
                # Parse JSON
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error analyzing image: {str(e)}")
            
    def calculate_health_score(self, nutrition_data):
        scores = {
            "calories": 1 if nutrition_data.get("calories", 0) <= self.thresholds["calories"] else 0,
            "sugar": 1 if nutrition_data.get("sugar", 0) <= self.thresholds["sugar"] else 0,
            "saturated_fat": 1 if nutrition_data.get("saturated_fat", 0) <= self.thresholds["saturated_fat"] else 0,
            "sodium": 1 if nutrition_data.get("sodium", 0) <= self.thresholds["sodium"] else 0,
            "protein": 1 if nutrition_data.get("protein", 0) >= self.thresholds["protein"] else 0
        }
        return {
            "total_score": sum(scores.values()) / len(scores) * 100,
            "component_scores": scores
        }

def get_analysis_prompt(image_type):
    if image_type == "Food Label":
        return """
        Analyze this nutrition label and extract the following information in JSON format:
        {
            "calories": number,
            "protein": number (in grams),
            "carbohydrates": number (in grams),
            "sugar": number (in grams),
            "fat": number (in grams),
            "saturated_fat": number (in grams),
            "sodium": number (in mg),
            "fiber": number (in grams),
            "serving_size": string
        }
        Ensure the response is only JSON, with no additional text or explanations.
        """
    else:
        return """
        Analyze this food image and:
        1. Identify all visible food items
        2. Estimate portion sizes
        3. Calculate approximate calories, protein, carbohydrates, and fat for each item
        
        Respond in JSON format:
        {
            "food_items": [
                {
                    "name": "item name",
                    "portion": "portion size",
                    "calories": number,
                    "protein": number (in grams),
                    "carbohydrates": number (in grams),
                    "fat": number (in grams)
                }
            ],
            "total_calories": number,
            "total_protein": number (in grams),
            "total_carbs": number (in grams),
            "total_fat": number (in grams)
        }
        Be specific about portions but don't include disclaimers about estimates.
        Only provide the JSON data, no additional text.
        """
