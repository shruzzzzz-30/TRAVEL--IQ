import openai
from flask import Flask, request, render_template, redirect, url_for, session
from dotenv import load_dotenv
import os
import logging
import re
from datetime import timedelta

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# Setup basic logging
logging.basicConfig(level=logging.DEBUG)

# Set session timeout
app.permanent_session_lifetime = timedelta(hours=1)

def generate_itinerary(destination, duration, activities, budget):
    try:
        activities_text = ', '.join(activities) if activities else "some interesting activities"

        # Request itinerary details from OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful and detailed travel assistant."},
                {"role": "user", "content": (
                    f"Create a {duration}-day detailed travel itinerary for {destination}. "
                    f"The budget is {budget}. Suggested activities include: {activities_text}. "
                    f"Provide daily costs for accommodation, meals, transportation, and activities. "
                    f"Highlight key landmarks, cultural spots, and any local travel tips."
                )}
            ]
        )

        # Validate response structure
        if not response.get('choices') or not response['choices'][0].get('message', {}).get('content'):
            logging.error("Invalid response from OpenAI API.")
            return "Error: Invalid response format from OpenAI."

        itinerary_text = response['choices'][0]['message']['content']
        logging.debug(f"Raw OpenAI response: {itinerary_text}")

        # Parse response into structured data
        itinerary_details = []
        days = re.split(r'\bDay (\d+):?\b', itinerary_text)[1:]  # Split on 'Day X' labels
        num_days = min(int(duration), len(days) // 2)  # Ensure only requested days are parsed

        for i in range(num_days):
            day_number = days[2 * i]
            day_content = days[2 * i + 1]

            logging.debug(f"Parsing Day {day_number}: {day_content[:200]}...")

            # Extracting costs
            cost_matches = re.findall(r'INR\s*(\d+)', day_content)
            accommodation_cost = int(cost_matches[0]) if len(cost_matches) > 0 else 0
            meals_cost = int(cost_matches[1]) if len(cost_matches) > 1 else 0
            activities_cost = int(cost_matches[2]) if len(cost_matches) > 2 else 0

            # Extracting activities
            activities_list = re.findall(r'•\s*([^\n]+)|(?:Visit|Explore|Enjoy)\s+([^\.\n]+)', day_content)
            activities_cleaned = [item[0].strip() or item[1].strip() for item in activities_list if item[0] or item[1]]

            # Adding day details
            day_details = {
                'day': f'Day {day_number}',
                'description': day_content.strip(),
                'accommodation_cost': accommodation_cost,
                'meals_cost': meals_cost,
                'activities_cost': activities_cost,
                'total_day_cost': accommodation_cost + meals_cost + activities_cost,
                'activities': activities_cleaned or ["Relax or enjoy free time."]
            }

            itinerary_details.append(day_details)

        logging.debug(f"Parsed itinerary details: {itinerary_details}")
        return itinerary_details

    except Exception as e:
        logging.error(f"Error generating itinerary: {str(e)}")
        return f"Error generating itinerary: {str(e)}"

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/index", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        destination = request.form.get("destination")
        duration = request.form.get("duration")
        budget = request.form.get("budget")
        activities_input = request.form.get("activities")
        
        # Handle activities input and split by commas if not empty
        activities = [activity.strip() for activity in activities_input.split(',')] if activities_input else []

        # Validate input fields
        if not destination or not duration or not budget:
            return render_template("index.html", error="Please fill in all fields.")
        
        # Validate duration and budget as positive numbers
        if not duration.isdigit() or int(duration) <= 0:
            return render_template("index.html", error="Duration must be a positive number.")
        if not budget.isdigit() or int(budget) <= 0:
            return render_template("index.html", error="Budget must be a positive number.")
        
        # Generate itinerary
        itinerary = generate_itinerary(destination, duration, activities, budget)
        logging.debug(f"Generated itinerary: {itinerary}")

        if isinstance(itinerary, str):  # Error handling
            return render_template("index.html", error=itinerary)
        
        # Save itinerary and duration in session
        session['itinerary'] = itinerary
        session['duration'] = duration
        return redirect(url_for('itinerary'))
    
    return render_template("index.html")

@app.route("/itinerary")
def itinerary():
    itinerary_details = session.get('itinerary', None)

    if not itinerary_details:
        return render_template("itinerary.html", error="No itinerary found. Please generate an itinerary first.")

    # Calculate total budget
    total_budget = sum(day['total_day_cost'] for day in itinerary_details if isinstance(day, dict))
    logging.debug(f"Total Budget: {total_budget}")

    return render_template("itinerary.html", itinerary=itinerary_details, total_budget=total_budget)

if __name__ == "__main__":
    app.run(debug=True)
