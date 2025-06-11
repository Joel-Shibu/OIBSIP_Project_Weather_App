import tkinter as tk
from tkinter import *
from tkinter import ttk, messagebox
from tkinter.constants import *
from PIL import Image, ImageTk
import requests
from io import BytesIO
import os
from dotenv import load_dotenv
import geocoder
from datetime import datetime

# Load API keys from .env
load_dotenv()
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
IPGEOLOCATION_API_KEY = os.getenv("IPGEOLOCATION_API_KEY")

# Initialize IPGeolocation API
ipgeo = None

# Color scheme
COLORS = {
    'primary': '#1e88e5',      # Main blue
    'primary_light': '#42a5f5',  # Lighter blue
    'primary_dark': '#1565c0',   # Darker blue
    'background': '#e3f2fd',     # Very light blue background
    'surface': '#ffffff',        # White surface
    'text_primary': '#0d47a1',   # Dark blue text
    'text_secondary': '#424242', # Dark gray text
    'accent': '#0288d1',         # Accent blue
    'border': '#bbdefb',         # Light blue border
    'success': '#2e7d32',        # Green for success messages
    'warning': '#f9a825',        # Yellow for warnings
    'error': '#c62828'           # Red for errors
}

# Fetch weather data
def get_weather(city):
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
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

# Fetch forecast data
def get_forecast(city):
    try:
        api_key = WEATHER_API_KEY
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&appid={api_key}"
        response = requests.get(url)
        data = response.json()

        if data.get("cod") != "200":
            print("Forecast API error:", data.get("message", "Unknown error"))
            return None

        daily_forecast = []
        seen_dates = set()

        for entry in data["list"]:
            dt_txt = entry["dt_txt"]  # format: "2025-06-11 12:00:00"
            if "12:00:00" in dt_txt:
                date_obj = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S")
                date_label = date_obj.strftime("%a, %d %b")  # "Wed, 11 Jun"
                if date_label not in seen_dates:
                    seen_dates.add(date_label)
                    daily_forecast.append({
                        "date": date_label,
                        "temp": entry["main"]["temp"],
                        "icon": entry["weather"][0]["icon"],
                        "weather": entry["weather"][0]["description"]
                    })

        print('Forecast API response:', data)
        return daily_forecast[:5]

    except Exception as e:
        print(f"Error fetching forecast: {e}")
        return None

# display forecast
def display_forecast_gui(forecast_data, parent_frame):
    try:
        print("Displaying forecast data:", forecast_data)
        
        # Clear any existing widgets in parent frame
        for widget in parent_frame.winfo_children():
            widget.destroy()
        
        # Main forecast container with subtle styling
        forecast_container = Frame(parent_frame, 
                                bg=COLORS['background'],
                                bd=0,
                                relief=FLAT,
                                padx=5,
                                pady=5)
        forecast_container.pack(fill=BOTH, expand=True, pady=(0, 10))
        forecast_container.pack_propagate(False)
        forecast_container.config(height=220)  # Fixed height for consistency
        
        # Title with subtle underline
        title_frame = Frame(forecast_container, bg=COLORS['background'])
        title_frame.pack(fill=X, pady=(0, 10), padx=5)
        
        title_label = Label(title_frame, 
                          text="5-DAY FORECAST", 
                          font=("Helvetica", 10, "bold"),
                          bg=COLORS['background'], 
                          fg=COLORS['primary_dark'],
                          anchor='w')
        title_label.pack(side=LEFT)
        
        # Add subtle separator line under title
        separator = Frame(title_frame, height=1, bg='#e0e0e0')
        separator.pack(side=BOTTOM, fill=X, pady=(5, 0))
        
        # Create a frame for the days with horizontal scrolling
        canvas_container = Frame(forecast_container, 
                              bg=COLORS['background'],
                              height=180)
        canvas_container.pack(fill=BOTH, expand=True)
        canvas_container.pack_propagate(False)
        
        # Create canvas with horizontal scrollbar
        canvas = Canvas(canvas_container, 
                      bg=COLORS['background'],
                      highlightthickness=0,
                      height=180)
        
        # Add horizontal scrollbar (only show if needed)
        x_scrollbar = ttk.Scrollbar(canvas_container, 
                                 orient=HORIZONTAL, 
                                 command=canvas.xview)
        
        canvas.configure(xscrollcommand=x_scrollbar.set)
        
        # Pack the canvas and scrollbar
        canvas.pack(side=TOP, fill=BOTH, expand=True)
        x_scrollbar.pack(side=BOTTOM, fill=X)
        
        # Create a frame inside the canvas to hold the days
        days_container = Frame(canvas, bg=COLORS['background'])
        
        # Calculate required width for all day frames
        day_width = 110  # Reduced width for better fit
        padding = 5      # Reduced padding between frames
        total_width = (day_width * 5) + (padding * 6)  # 5 days, 6 gaps
        
        # Create the window in the canvas for the days container
        canvas.create_window((0, 0), window=days_container, anchor='nw', width=total_width, height=180)
        
        # Configure day frame style
        day_style = {
            'bg': '#f8f9fa',  # Light gray background for cards
            'bd': 0,
            'relief': 'flat',
            'padx': 8,
            'pady': 10,
            'width': day_width,
            'height': 150  # Fixed height for day frames
        }

        # Create day frames
        for i, day in enumerate(forecast_data[:5]):  # Only show 5 days
            # Create day frame with subtle shadow effect
            day_frame = Frame(days_container, **day_style)
            day_frame.grid(row=0, column=i, padx=(0, padding) if i < 4 else 0, sticky='nsew', pady=5)
            day_frame.grid_propagate(False)
            
            # Configure column weights for the days container
            days_container.columnconfigure(i, weight=1)
            
            # Date with better formatting
            try:
                date_obj = datetime.strptime(day['date'], '%Y-%m-%d')
                day_name = date_obj.strftime('%A')  # Full day name (e.g., Monday)
                day_num = date_obj.strftime('%d').lstrip('0')  # Remove leading zero
                month_name = date_obj.strftime('%B')  # Full month name
                full_date = date_obj.strftime('%d %b %Y')  # e.g., "11 Jun 2023"
                
                # Create a frame for date with better styling
                date_frame = Frame(day_frame, bg='#f0f2f5', bd=0)
                date_frame.pack(fill=X, pady=(0, 5))
                
                # Full day name (e.g., "Monday")
                Label(date_frame, 
                     text=day_name.upper(), 
                     font=("Helvetica", 8, "bold"),
                     bg='#f0f2f5',
                     fg=COLORS['primary'],
                     justify='center').pack(fill=X, pady=(0, 1))
                
                # Day number (larger and bolder)
                Label(date_frame, 
                     text=day_num, 
                     font=("Helvetica", 20, "bold"),
                     bg='#f0f2f5',
                     fg=COLORS['text_primary'],
                     justify='center').pack(fill=X)
                
                # Month and year (smaller, below day number)
                Label(date_frame, 
                     text=f"{month_name} {date_obj.strftime('%Y')}", 
                     font=("Helvetica", 8),
                     bg='#f0f2f5',
                     fg=COLORS['text_secondary'],
                     justify='center').pack(fill=X, pady=(0, 3))
                
            except Exception as e:
                print(f"Error formatting date: {e}")
                date_str = day.get('date', 'N/A')
                Label(day_frame, 
                     text=date_str, 
                     font=("Helvetica", 8),
                     bg='#f8f9fa',
                     fg=COLORS['error'],
                     justify='center').pack(fill=X, pady=5)
            
            # Weather icon with better centering
            icon_frame = Frame(day_frame, bg='#f8f9fa')
            icon_frame.pack(fill=X, pady=(5, 0))
            
            icon_code = day.get('icon', '')
            icon_path = os.path.join("icons", f"{icon_code}.png")
            
            try:
                if os.path.exists(icon_path):
                    icon_image = Image.open(icon_path)
                    icon_image = icon_image.resize((50, 50), Image.Resampling.LANCZOS)
                    icon_photo = ImageTk.PhotoImage(icon_image)
                    icon_label = Label(icon_frame, image=icon_photo, bg='#f8f9fa')
                    icon_label.image = icon_photo
                    icon_label.pack()
                else:
                    print(f"Icon not found: {icon_path}")
                    Label(icon_frame, 
                         text="☀️", 
                         font=("Arial", 24), 
                         bg='#f8f9fa').pack()
            except Exception as e:
                print(f"Error loading icon: {e}")
                Label(icon_frame, 
                     text="☀️", 
                     font=("Arial", 24), 
                     bg='#f8f9fa').pack()
            
            # Temperature with better styling
            temp_frame = Frame(day_frame, bg='#f8f9fa')
            temp_frame.pack(fill=X, pady=(5, 0))
            
            temp = day.get('temp', 'N/A')
            temp_str = f"{int(round(float(temp), 0))}°" if temp != 'N/A' else temp
            
            Label(temp_frame, 
                 text=temp_str, 
                 font=("Helvetica", 18, "bold"),
                 bg='#f8f9fa',
                 fg=COLORS['primary_dark']).pack()
            
            # Weather description with better wrapping
            weather_frame = Frame(day_frame, bg='#f8f9fa')
            weather_frame.pack(fill=X, pady=(5, 0))
            
            weather_desc = day.get('weather', 'N/A')
            desc_label = Label(weather_frame, 
                             text=str(weather_desc).title(), 
                             font=("Helvetica", 8), 
                             bg='#f8f9fa',
                             fg=COLORS['text_secondary'],
                             wraplength=day_width-16,  # Account for padding
                             justify='center')
            desc_label.pack(fill=X)
        
        # Update the scroll region after all widgets are added
        days_container.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        
        # Only show scrollbar if needed
        if total_width > canvas.winfo_width():
            x_scrollbar.pack(side=BOTTOM, fill=X)
        
    except Exception as e:
        print(f"Error in display_forecast_gui: {e}")
        import traceback
        traceback.print_exc()

# Update UI
def show_weather():
    try:
        # Clear previous weather display
        for widget in weather_container.winfo_children():
            widget.destroy()
            
        city = city_entry.get().strip()
        if not city:
            messagebox.showinfo("Info", "Please enter a city or use the Auto Detect button")
            return

        data = get_weather(city)
        if not data:
            messagebox.showerror("Error", "Could not retrieve weather data")
            return

        # Main container with padding
        main_container = Frame(weather_container, bg=COLORS['background'], padx=20, pady=20)
        main_container.pack(fill=BOTH, expand=True)
        
        # Current weather section
        current_weather_frame = Frame(main_container, 
                                   bg=COLORS['surface'],
                                   bd=2,
                                   relief=GROOVE,
                                   padx=20,
                                   pady=20)
        current_weather_frame.pack(fill=X, pady=(0, 20))
        
        # Top row with city and icon
        top_row = Frame(current_weather_frame, bg=COLORS['surface'])
        top_row.pack(fill=X, pady=(0, 15))
        
        # City and date
        city_date_frame = Frame(top_row, bg=COLORS['surface'])
        city_date_frame.pack(side=LEFT, fill=BOTH, expand=True)
        
        city_label = Label(city_date_frame, 
                         text=f"{data['name']}", 
                         font=("Helvetica", 24, "bold"), 
                         bg=COLORS['surface'],
                         fg=COLORS['text_primary'])
        city_label.pack(anchor='w')

        current_date = datetime.now().strftime("%A, %B %d, %Y")
        date_label = Label(city_date_frame, 
                         text=current_date,
                         font=("Helvetica", 12),
                         bg=COLORS['surface'],
                         fg=COLORS['text_secondary'])
        date_label.pack(anchor='w', pady=(0, 10))
        
        # Weather icon
        icon_code = data["weather"][0]["icon"]
        icon_path = os.path.join("icons", f"{icon_code}.png")
        try:
            if os.path.exists(icon_path):
                icon_image = Image.open(icon_path)
                icon_image = icon_image.resize((100, 100), Image.Resampling.LANCZOS)
                icon_photo = ImageTk.PhotoImage(icon_image)
                icon_label = Label(top_row, 
                                 image=icon_photo, 
                                 bg=COLORS['surface'])
                icon_label.image = icon_photo
                icon_label.pack(side=RIGHT, padx=10)
                print(f"Successfully loaded icon: {icon_path}")
            else:
                print(f"Icon file not found: {icon_path}")
        except Exception as e:
            print(f"Error loading icon: {e}")
        
        # Weather details
        details_frame = Frame(current_weather_frame, bg=COLORS['surface'])
        details_frame.pack(fill=X, pady=10)
        
        # Left side - Temperature and condition
        temp_frame = Frame(details_frame, bg=COLORS['surface'])
        temp_frame.pack(side=LEFT, fill=BOTH, expand=True)
        
        temp_value = Label(temp_frame, 
                         text=f"{data['main']['temp']}°C",
                         font=("Helvetica", 42, "bold"),
                         bg=COLORS['surface'],
                         fg=COLORS['primary_dark'])
        temp_value.pack(anchor='w')
        
        condition = data["weather"][0]["description"].title()
        condition_label = Label(temp_frame,
                              text=condition,
                              font=("Helvetica", 14),
                              bg=COLORS['surface'],
                              fg=COLORS['text_secondary'])
        condition_label.pack(anchor='w', pady=(5, 0))
        
        # Right side - Additional details
        details_right = Frame(details_frame, bg=COLORS['surface'])
        details_right.pack(side=RIGHT, fill=Y)
        
        def add_detail(parent, label, value, unit=""):
            frame = Frame(parent, bg=COLORS['surface'])
            frame.pack(fill=X, pady=2)
            Label(frame, text=f"{label}:", 
                 font=("Helvetica", 10), 
                 bg=COLORS['surface'],
                 fg=COLORS['text_secondary']).pack(side=LEFT)
            Label(frame, text=f" {value}{unit}", 
                 font=("Helvetica", 10, "bold"),
                 bg=COLORS['surface'],
                 fg=COLORS['text_primary']).pack(side=RIGHT)
        
        add_detail(details_right, "Feels Like", f"{data['main']['feels_like']}°C")
        add_detail(details_right, "Humidity", f"{data['main']['humidity']}%")
        add_detail(details_right, "Wind", f"{data['wind']['speed']} m/s")
        add_detail(details_right, "Pressure", f"{data['main']['pressure']} hPa")
        
        # Add sunrise/sunset if available
        if 'sunrise' in data['sys'] and 'sunset' in data['sys']:
            sunrise = datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M')
            sunset = datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M')
            
            sun_frame = Frame(current_weather_frame, bg=COLORS['surface'], pady=10)
            sun_frame.pack(fill=X, pady=(10, 0))
            
            Label(sun_frame, text=f"☀️ {sunrise}  •  🌙 {sunset}",
                 font=("Helvetica", 12),
                 bg=COLORS['surface'],
                 fg=COLORS['text_secondary']).pack(anchor='center')

        # Get and display forecast in a separate frame
        forecast_frame = Frame(main_container, bg=COLORS['background'])
        forecast_frame.pack(fill=BOTH, expand=True)
        
        forecast_data = get_forecast(city)
        if forecast_data:
            display_forecast_gui(forecast_data, forecast_frame)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to retrieve weather data: {str(e)}")
        print(f"Error in show_weather: {e}")

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
        
    def detect_with_ipgeolocation():
        if not IPGEOLOCATION_API_KEY:
            return None, "IPGeolocation API key not configured"
        try:
            response = requests.get(
                'https://api.ipgeolocation.io/ipgeo',
                params={'apiKey': IPGEOLOCATION_API_KEY},
                timeout=3
            )
            data = response.json()
            if 'city' in data and data['city']:
                return data['city'], None
            return None, data.get('message', 'Unknown error from IPGeolocation')
        except Exception as e:
            return None, str(e)

    # Show loading state
    auto_detect_btn.config(state=tk.DISABLED, text="Detecting...")
    root.update()
    
    try:
        # Try multiple detection methods
        detection_methods = [
            ("IPGeolocation", detect_with_ipgeolocation) if IPGEOLOCATION_API_KEY else None,
            ("Geocoder", detect_with_geocoder),
            ("ipapi", detect_with_ipapi),
            ("ipinfo", detect_with_ipinfo)
        ]
        
        # Remove None values (in case IPGeolocation is not configured)
        detection_methods = [m for m in detection_methods if m is not None]
        
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
root.title("Weather App")
root.geometry("1200x800")
root.configure(bg=COLORS['background'])

# Set application style
style = ttk.Style()
style.configure('TFrame', background=COLORS['background'])
style.configure('TLabel', background=COLORS['background'])
style.configure('TButton', 
               font=('Helvetica', 11, 'bold'),
               padding=6)

# Main container
main_frame = Frame(root, bg=COLORS['background'], name='main_frame')
main_frame.pack(fill=BOTH, expand=True, padx=40, pady=30)

# Header
header_frame = Frame(main_frame, bg=COLORS['background'])
header_frame.pack(fill=X, pady=(0, 20))

# App title with weather icon
title_frame = Frame(header_frame, bg=COLORS['background'])
title_frame.pack(fill=X)  

app_title = Label(title_frame, 
                 text="Weather Forecast",
                 font=("Helvetica", 32, "bold"),
                 bg=COLORS['background'],
                 fg=COLORS['primary_dark'])
app_title.pack(expand=True)  

# Add a subtle line under the title
title_underline = Frame(header_frame, 
                      height=4, 
                      bg=COLORS['primary_light'])
title_underline.pack(fill=X, pady=(10, 0))

# Search container
search_container = Frame(main_frame, bg=COLORS['background'])
search_container.pack(fill=X, pady=(20, 15))

# City input frame
city_frame = Frame(search_container, name='city_frame', bg=COLORS['background'])
city_frame.pack(side=LEFT, fill=X, expand=True)

city_label = Label(city_frame, 
                  text="Enter City:", 
                  font=("Helvetica", 14, "bold"), 
                  bg=COLORS['background'],
                  fg=COLORS['text_primary'])
city_label.pack(side=LEFT, padx=(0, 10), pady=5)

city_entry = Entry(city_frame, 
                  font=("Helvetica", 14), 
                  width=30,
                  bd=2,
                  relief=GROOVE,
                  highlightthickness=0)
city_entry.pack(side=LEFT, padx=(0, 10), ipady=6)
city_entry.focus()

# Button frame
button_frame = Frame(search_container, name='button_frame', bg=COLORS['background'])
button_frame.pack(side=LEFT, padx=(15, 0))

search_btn = Button(button_frame, 
                   text="Get Weather", 
                   command=show_weather,
                   bg=COLORS['primary'], 
                   fg='white', 
                   activebackground=COLORS['primary_dark'],
                   activeforeground='white',
                   font=("Helvetica", 12, "bold"),
                   padx=20, 
                   pady=6, 
                   bd=0,
                   relief=FLAT)
search_btn.pack(side=LEFT, padx=(0, 10))

auto_detect_btn = Button(button_frame, 
                        text="Auto Detect", 
                        command=auto_detect_location,
                        bg=COLORS['accent'], 
                        fg='white',
                        activebackground=COLORS['primary_dark'],
                        activeforeground='white',
                        font=("Helvetica", 12, "bold"),
                        padx=20, 
                        pady=6, 
                        bd=0,
                        relief=FLAT)
auto_detect_btn.pack(side=LEFT)

# Weather info container
weather_container = Frame(main_frame, bg=COLORS['background'])
weather_container.pack(fill=BOTH, expand=True, pady=(10, 0))

root.mainloop()
