import tkinter as tk
from tkinter import messagebox
import requests
import os
from dotenv import load_dotenv
from PIL import Image, ImageTk
from io import BytesIO

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("WEATHER_API_KEY")

# Fetch weather data
def get_weather(city):
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        messagebox.showerror("Error", f"HTTP Error: {http_err}")
    except Exception as err:
        messagebox.showerror("Error", f"Error: {err}")
    return None

# Update UI
def show_weather():
    city = city_entry.get()
    data = get_weather(city)
    if data:
        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        condition = data["weather"][0]["description"].title()
        wind_speed = data["wind"]["speed"]

        result_text.set(f"""
📍 {data['name']}
🌡️ Temperature: {temperature}°C
💧 Humidity: {humidity}%
🌤️ Condition: {condition}
🌬️ Wind: {wind_speed} m/s
""")

        # Optional: Weather icon
        icon_code = data["weather"][0]["icon"]
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
        icon_response = requests.get(icon_url)
        icon_image = Image.open(BytesIO(icon_response.content))
        icon_photo = ImageTk.PhotoImage(icon_image)
        icon_label.config(image=icon_photo)
        icon_label.image = icon_photo

# GUI Setup
root = tk.Tk()
root.title("Weather App 🌤️")
root.geometry("400x400")
root.resizable(False, False)
root.configure(bg="#e0f7fa")

city_entry = tk.Entry(root, font=("Segoe UI", 14), justify="center")
city_entry.pack(pady=20)
city_entry.focus()

search_button = tk.Button(root, text="Get Weather", font=("Segoe UI", 12), command=show_weather)
search_button.pack()

result_text = tk.StringVar()
result_label = tk.Label(root, textvariable=result_text, font=("Segoe UI", 12), justify="center", bg="#e0f7fa")
result_label.pack(pady=20)

icon_label = tk.Label(root, bg="#e0f7fa")
icon_label.pack()

root.mainloop()
