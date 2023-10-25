import json
from flask import Flask, Response, request
import requests
from datetime import datetime
import os

# Constants for API endpoints and keys
api_endpoint = "https://api.open-meteo.com/v1/forecast"
geo_url = "https://api.openweathermap.org/geo/1.0/direct"
geo_url_api_key = os.environ.get("GEO_URL_API_KEY")

app = Flask(__name__)

def post_webhook_dialogflow():
    """Handle the POST request from Dialogflow and return a webhook response."""
    body = request.get_json(silent=True)
    fulfillment = body['fulfillmentInfo']['tag']
    parameters = {}
    for key, value in body['sessionInfo']['parameters'].items():
        parameters[key] = value
    msg = get_message(fulfillment, parameters)
    webhook_response = answer_webhook(msg)
    return webhook_response

@app.route('/my_webhook', methods=['POST'])
def my_webhook():
    """Route for Dialogflow webhook."""
    return post_webhook_dialogflow()

def get_message(fulfillment, parameters):
    """Generate a response message based on the fulfillment tag and parameters."""
    if fulfillment == "get_weather":
        year = int(parameters['date-time']['year'])
        month = int(parameters['date-time']['month'])
        day = int(parameters['date-time']['day'])
        date = datetime(year, month, day)
        f_date = format_date(date)
        days_from_now = (date - datetime.now()).days + 1
        if days_from_now > 7:
            return "We can only forecast up to 6 days in advance."
        elif days_from_now < 0:
            return "We can't give a weather forecast for past dates."
        city = str(parameters['geo-city'])
        weather_info = weather(city, days_from_now)
        if isinstance(weather_info, str):
            msg = weather_info
        else:
            temperature_max = weather_info["temperature_max"]
            temperature_min = weather_info["temperature_min"]
            msg = f"The weather forecast for {city} on {f_date} is min {temperature_min}°C and max {temperature_max}°C."
        return msg

def answer_webhook(msg):
    """Generate a webhook response with the given message."""
    message = {
        "fulfillment_response": {
            "messages": [
                {
                    "text": {
                        "text": [msg]
                    }
                }
            ]
        }
    }
    return Response(json.dumps(message), 200, mimetype='application/json')

def get_city_coordinates(city):
    """Get the latitude and longitude of a city using the OpenWeatherMap API."""
    geo_params = {
        "q": city,
        "limit": 1,
        "appid": geo_url_api_key
    }
    geo_response = requests.get(geo_url, params=geo_params)
    if geo_response.status_code == 200:
        geo_data = geo_response.json()
        if geo_data:
            return geo_data[0]["lat"], geo_data[0]["lon"]
    return None

def get_weather_forecast(lat, lon, cnt=0):
    """Get the weather forecast for a location using the Open Meteo API."""
    weather_params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": "Europe/London"
    }
    weather_response = requests.get(api_endpoint, params=weather_params)
    if weather_response.status_code == 200:
        weather_data = weather_response.json()
        if "daily" in weather_data:
            if cnt < len(weather_data["daily"]["time"]):
                temperature_max = weather_data["daily"]["temperature_2m_max"][cnt]
                temperature_min = weather_data["daily"]["temperature_2m_min"][cnt]
                return {
                    "date": weather_data["daily"]["time"][cnt],
                    "temperature_max": temperature_max,
                    "temperature_min": temperature_min
                }
            else:
                return "We can only forecast up to 6 days in advance."
    return None

def weather(city, cnt):
    """Get the weather forecast for a city for a specific number of days from now."""
    lat, lon = get_city_coordinates(city)
    if lat is not None and lon is not None:
        forecast = get_weather_forecast(lat, lon, cnt)
        if forecast:
            return forecast
    return "City not found or weather forecast not available."

def format_date(date):
    """Format a date as 'Month day, year'."""
    formatted_date = date.strftime("%B %d, %Y")
    return formatted_date

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8081, debug=True)
