import tkinter as tk
from tkinter import messagebox
import requests
import os
from dotenv import load_dotenv
from PIL import Image, ImageTk
from io import BytesIO
import geocoder
from tkinter import simpledialog


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
    if not city:
        messagebox.showinfo("Info", "Please enter a city or use the Auto Detect button")
        return
    data = get_weather(city)
    if data:
        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        condition = data["weather"][0]["description"].title()
        wind_speed = data["wind"]["speed"]

        result_text.set(f"""
 {data['name']}
 Temperature: {temperature}°C
 Humidity: {humidity}%
 Condition: {condition}
 Wind: {wind_speed} m/s
""")

        # Weather icon
        icon_code = data["weather"][0]["icon"]
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
        icon_response = requests.get(icon_url)
        icon_image = Image.open(BytesIO(icon_response.content))
        icon_photo = ImageTk.PhotoImage(icon_image)
        icon_label.config(image=icon_photo)
        icon_label.image = icon_photo

def auto_detect_location():
    def detect_with_geocoder():
        try:
            g = geocoder.ip('me')
            if g.ok and g.city:
                return g.city, None
        except Exception as e:
            return None, str(e)
        return None, "Geocoder service unavailable"
    
    def detect_with_ipapi():
        try:
            response = requests.get('https://ipapi.co/json/', timeout=3)
            data = response.json()
            if 'city' in data and data['city']:
                return data['city'], None
        except Exception as e:
            return None, str(e)
        return None, "ipapi service unavailable"
        
    def detect_with_ipinfo():
        try:
            response = requests.get('https://ipinfo.io/json', timeout=3)
            data = response.json()
            if 'city' in data and data['city']:
                return data['city'], None
        except Exception as e:
            return None, str(e)
        return None, "ipinfo service unavailable"

    # Show loading state
    auto_detect_btn.config(state=tk.DISABLED, text="Detecting...")
    root.update()
    
    try:
        # Try multiple detection methods
        detection_methods = [
            ("Geocoder", detect_with_geocoder),
            ("ipapi", detect_with_ipapi),
            ("ipinfo", detect_with_ipinfo)
        ]
        
        last_error = "No detection methods available"
        for service_name, method in detection_methods:
            city, error = method()
            if city:
                city_entry.delete(0, tk.END)
                city_entry.insert(0, city)
                show_weather()
                break
            last_error = f"{service_name} failed: {error}"
        else:
            messagebox.showerror(
                "Location Error",
                f"Could not detect your location.\n\n"
                f"Please enter your city manually.\n"
                f"Last error: {last_error}"
            )
    except Exception as e:
        messagebox.showerror("Error", f"Failed to detect location: {str(e)}")
    finally:
        auto_detect_btn.config(state=tk.NORMAL, text="Auto Detect")

# GUI Setup
root = tk.Tk()
root.title("Weather App ")
root.geometry("400x450")
root.resizable(False, False)
root.configure(bg="#e0f7fa")

# Input frame
input_frame = tk.Frame(root, bg="#e0f7fa")
input_frame.pack(pady=20)

city_entry = tk.Entry(input_frame, font=("Segoe UI", 14), justify="center", width=20)
city_entry.pack(side=tk.LEFT, padx=5)

# Buttons frame
button_frame = tk.Frame(root, bg="#e0f7fa")
button_frame.pack(pady=5)

search_button = tk.Button(button_frame, text="Search", font=("Segoe UI", 10), 
                         command=show_weather, bg="#4CAF50", fg="white")
search_button.pack(side=tk.LEFT, padx=5)

auto_detect_btn = tk.Button(button_frame, text="Auto Detect", font=("Segoe UI", 10), 
                           command=auto_detect_location, bg="#2196F3", fg="white")
auto_detect_btn.pack(side=tk.LEFT, padx=5)

result_text = tk.StringVar()
result_label = tk.Label(root, textvariable=result_text, font=("Segoe UI", 12), justify="center", bg="#e0f7fa")
result_label.pack(pady=20)

icon_label = tk.Label(root, bg="#e0f7fa")
icon_label.pack()

root.mainloop()
