import requests
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get the API key from .env
API_KEY = os.getenv("WEATHER_API_KEY")

def get_weather(city):
    if not API_KEY:
        print("API key not found. Check your .env file.")
        return

    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        print("\n Weather in", data['name'])
        print(" Temperature:", data['main']['temp'], "°C")
        print(" Humidity:", data['main']['humidity'], "%")
        print(" Condition:", data['weather'][0]['description'].title())
        print(" Wind Speed:", data['wind']['speed'], "m/s")

    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            print("City not found. Please check the spelling.")
        else:
            print(f" HTTP error occurred: {http_err}")
    except Exception as err:
        print(f" Other error occurred: {err}")

if __name__ == "__main__":
    city = input("Enter city name: ")
    get_weather(city)
