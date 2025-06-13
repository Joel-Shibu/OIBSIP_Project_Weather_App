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

# Unit state (True for Celsius, False for Fahrenheit)
use_celsius = True

# Theme state (True for light, False for dark)
light_theme = True

# Color schemes for light and dark themes
THEMES = {
    'light': {
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
        'error': '#c62828',          # Red for errors
        'button_text': 'white',      # Text color for buttons
        'toggle_bg': '#42a5f5',      # Toggle button background
        'toggle_fg': 'white',        # Toggle button text color
        'card_bg': '#ffffff',        # Card background
        'card_fg': '#0d47a1',        # Card text color
        'forecast_bg': '#f5f9ff',    # Forecast background
    },
    'dark': {
        'primary': '#1976d2',      # Main blue
        'primary_light': '#42a5f5',  # Lighter blue
        'primary_dark': '#0d47a1',   # Darker blue
        'background': '#121212',     # Very dark background
        'surface': '#1e1e1e',        # Dark surface
        'text_primary': '#e3f2fd',   # Light blue text
        'text_secondary': '#b0bec5', # Light gray text
        'accent': '#29b6f6',         # Brighter accent blue
        'border': '#0d47a1',         # Dark blue border
        'success': '#66bb6a',        # Light green
        'warning': '#ffca28',        # Light yellow
        'error': '#ef5350',          # Light red
        'button_text': '#ffffff',    # White text for buttons
        'toggle_bg': '#0d47a1',      # Darker blue for toggle
        'toggle_fg': 'white',        # Toggle button text color
        'card_bg': '#1e1e1e',        # Dark card background
        'card_fg': '#e3f2fd',        # Light text for cards
        'forecast_bg': '#1e1e1e',    # Dark forecast background
    }
}

# Current theme colors
COLORS = THEMES['light'].copy()

def toggle_units():
    """Toggle between Celsius and Fahrenheit"""
    global use_celsius
    use_celsius = not use_celsius
    unit_toggle_btn.config(text="🌡️ °F" if use_celsius else "🌡️ °C")
    if city_entry.get().strip():
        show_weather()

def convert_temp(temp_c):
    """Convert temperature between Celsius and Fahrenheit"""
    if use_celsius:
        return temp_c, "°C"
    else:
        return (temp_c * 9/5) + 32, "°F"

def toggle_theme():
    """Toggle between light and dark themes"""
    global light_theme, COLORS
    light_theme = not light_theme
    theme = 'light' if light_theme else 'dark'
    COLORS = THEMES[theme].copy()
    

    theme_btn.config(text="🌞" if light_theme else "🌙")
    
    # Update all UI elements
    update_theme()
    
    # Refresh weather display to update colors
    if city_entry.get().strip():
        show_weather()

def update_theme():
    """Update all UI elements with current theme colors"""
    # Update root window
    root.configure(bg=COLORS['background'])
    
    # Update main container and frames
    for frame in [main_frame, header_frame, title_frame, search_container, 
                 city_frame, button_frame, weather_container]:
        frame.config(bg=COLORS['background'])
    
    # Update title and labels
    app_title.config(bg=COLORS['background'], fg=COLORS['primary_dark'])
    title_underline.config(bg=COLORS['primary_light'])
    city_label.config(bg=COLORS['background'], fg=COLORS['text_primary'])
    
    # Update entry field
    city_entry.config(
        bg=COLORS['surface'],
        fg=COLORS['text_primary'],
        insertbackground=COLORS['text_primary']
    )
    
    # Update buttons
    for btn in [search_btn, auto_detect_btn, unit_toggle_btn, theme_btn]:
        btn.config(
            bg=COLORS['primary_light'] if btn == unit_toggle_btn else COLORS['accent'] if btn == auto_detect_btn else COLORS['primary'],
            fg=COLORS['button_text'],
            activebackground=COLORS['primary_dark'],
            activeforeground=COLORS['button_text']
        )
    
    # Update theme button specifically
    theme_btn.config(bg=COLORS['toggle_bg'])

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
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&appid={api_key}&cnt=40"  # Request 40 entries (5 days * 8 per day)
        response = requests.get(url)
        data = response.json()

        if data.get("cod") != "200":
            print("Forecast API error:", data.get("message", "Unknown error"))
            return None

        daily_forecast = []
        seen_dates = set()
        
        print(f"Raw forecast data for {city}:", data)  # Debug print

        for entry in data.get("list", []):
            try:
                # Parse the date from the entry
                dt_txt = entry.get("dt_txt", "")
                if not dt_txt:
                    continue
                    
                # Parse the full datetime
                dt = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%Y-%m-%d")  # Just the date part
                
                # Skip if we already have this date
                if date_str in seen_dates:
                    continue
                    
                # Add to seen dates and create forecast entry
                seen_dates.add(date_str)
                daily_forecast.append({
                    "date": dt.strftime("%a, %d %b"),  # Format as "Wed, 11 Jun"
                    "temp": entry.get("main", {}).get("temp", "N/A"),
                    "icon": entry.get("weather", [{}])[0].get("icon", "02d"),
                    "weather": entry.get("weather", [{}])[0].get("description", "N/A")
                })
                
                print(f"Added forecast for {date_str}:", daily_forecast[-1])  # Debug print
                
                # Stop when we have 5 days
                if len(daily_forecast) >= 5:
                    break
                    
            except Exception as e:
                print(f"Error processing forecast entry: {e}")
                continue

        print('Processed forecast data:', daily_forecast)  # Debug print
        return daily_forecast

    except Exception as e:
        print(f"Error in get_forecast: {e}")
        import traceback
        traceback.print_exc()
        return None

# display forecast
def display_forecast_gui(forecast_data, parent_frame):
    try:
        print("Displaying forecast data:", forecast_data)  # Debug print
        
        # Clear any existing widgets in parent frame
        for widget in parent_frame.winfo_children():
            widget.destroy()
        
        if not forecast_data or len(forecast_data) == 0:
            print("No forecast data to display")
            return
        
        # Main forecast container with subtle styling
        forecast_container = Frame(parent_frame, 
                                bg=COLORS['background'],
                                bd=0,
                                relief=FLAT,
                                padx=5,
                                pady=0)
        forecast_container.pack(fill=BOTH, expand=True, pady=(0, 5))
        forecast_container.pack_propagate(False)
        forecast_container.config(height=180)  # Reduced height from 220
        
        # Title with subtle underline
        title_frame = Frame(forecast_container, bg=COLORS['background'])
        title_frame.pack(fill=X, pady=(0, 5))  # Reduced padding
        
        title_label = Label(title_frame, 
                          text="5-DAY FORECAST", 
                          font=("Helvetica", 9, "bold"),  # Smaller font
                          bg=COLORS['background'], 
                          fg=COLORS['primary_dark'],
                          anchor='center')
        title_label.pack(fill=X)
        
        # Add subtle separator line under title
        separator = Frame(title_frame, height=1, bg=COLORS['primary_light'])
        separator.pack(side=BOTTOM, fill=X, pady=(3, 0))  # Reduced padding
        
        # Create a frame for the days with horizontal scrolling
        canvas_container = Frame(forecast_container, 
                              bg=COLORS['background'],
                              height=150)  # Reduced height
        canvas_container.pack(fill=BOTH, expand=True)
        canvas_container.pack_propagate(False)
        
        # Create canvas with horizontal scrollbar
        canvas = Canvas(canvas_container, 
                      bg=COLORS['background'],
                      highlightthickness=0,
                      height=150)  # Reduced height
        
        # Add horizontal scrollbar (only show if needed)
        x_scrollbar = ttk.Scrollbar(canvas_container, 
                                 orient=HORIZONTAL, 
                                 command=canvas.xview)
        
        canvas.configure(xscrollcommand=x_scrollbar.set)
        
        # Pack the canvas and scrollbar
        canvas.pack(side=TOP, fill=BOTH, expand=True)
        
        # Create a frame inside the canvas to hold the days
        days_container = Frame(canvas, bg=COLORS['background'])
        
        # Calculate required width for all day frames
        day_width = 100  # Reduced from 120
        padding = 5      # Reduced padding between frames
        try:
            total_width = (day_width * 5) + (padding * 4)  # 5 days, 4 gaps
            print(f"DEBUG: day_width={day_width}, padding={padding}, total_width={total_width} (type: {type(total_width)})")
        except Exception as e:
            print(f"DEBUG ERROR calculating total_width: {e}")
        # Create the window in the canvas for the days container
        try:
            canvas.create_window((0, 0), window=days_container, anchor='nw', width=total_width, height=150)
        except Exception as e:
            print(f"DEBUG ERROR in create_window: {e}")
        
        # Configure day frame style - more compact
        day_style = {
            'bg': COLORS['card_bg'],
            'bd': 1,
            'relief': 'groove',
            'padx': 5,    # Reduced padding
            'pady': 5,    # Reduced padding
            'width': day_width,
            'height': 130  # Reduced height
        }

        # Create day frames for each forecast day
        for i, day in enumerate(forecast_data[:5]):  # Only show 5 days
            try:
                # Create day frame with subtle shadow effect
                day_frame = Frame(days_container, **day_style)
                day_frame.grid(row=0, column=i, padx=(0, padding) if i < 4 else 0, sticky='nsew', pady=2)
                day_frame.grid_propagate(False)
                
                # Configure column weights for the days container
                days_container.columnconfigure(i, weight=1)
                
                # Date with better formatting
                date_parts = day['date'].split(',')
                day_name = date_parts[0].strip()  # e.g., "Wed"
                day_num = date_parts[1].strip().split()[0]  # e.g., "11"
                month_name = date_parts[1].strip().split()[1]  # e.g., "Jun"
                
                # Create a frame for date with better styling
                date_frame = Frame(day_frame, bg=COLORS['card_bg'], bd=0)
                date_frame.pack(fill=X, pady=(0, 2))  # Reduced padding
                
                # Day name (e.g., "WED")
                Label(date_frame, 
                     text=day_name.upper(), 
                     font=("Helvetica", 8, "bold"),  # Smaller font
                     bg=COLORS['card_bg'],
                     fg=COLORS['primary'],
                     justify='center').pack(fill=X)
                
                # Day number (e.g., "11")
                Label(date_frame, 
                     text=day_num, 
                     font=("Helvetica", 16, "bold"),  # Smaller font
                     bg=COLORS['card_bg'],
                     fg=COLORS['text_primary'],
                     justify='center').pack(fill=X)
                
                # Month name (e.g., "JUN")
                Label(date_frame, 
                     text=month_name.upper(), 
                     font=("Helvetica", 8),  # Smaller font
                     bg=COLORS['card_bg'],
                     fg=COLORS['text_secondary'],
                     justify='center').pack(fill=X, pady=(0, 2))  # Reduced padding
                
                # Weather icon with better centering
                icon_frame = Frame(day_frame, bg=COLORS['card_bg'])
                icon_frame.pack(fill=X, pady=0)  # Removed vertical padding
                
                icon_code = day.get('icon', '')
                icon_path = os.path.join("icons", f"{icon_code}.png")
                
                try:
                    if os.path.exists(icon_path):
                        icon_image = Image.open(icon_path)
                        icon_image = icon_image.resize((40, 40), Image.Resampling.LANCZOS)  # Smaller icon
                        icon_photo = ImageTk.PhotoImage(icon_image)
                        icon_label = Label(icon_frame, image=icon_photo, bg=COLORS['card_bg'])
                        icon_label.image = icon_photo  # Keep a reference
                        icon_label.pack()
                    else:
                        # Fallback to text emoji
                        Label(icon_frame, 
                             text="☀️", 
                             font=("Arial", 16),  # Smaller emoji
                             bg=COLORS['card_bg']).pack()
                except Exception as e:
                    print(f"Error loading icon: {e}")
                    # Fallback to text emoji
                    Label(icon_frame, 
                         text="☀️", 
                         font=("Arial", 16),  # Smaller emoji
                         bg=COLORS['card_bg']).pack()
                
                # Temperature
                temp_frame = Frame(day_frame, bg=COLORS['card_bg'])
                temp_frame.pack(fill=X, pady=(0, 0))  # Removed vertical padding
                
                try:
                    temp = day.get('temp', 0)
                    if isinstance(temp, (int, float)):
                        temp_str = f"{int(round(float(temp), 0))}°C"
                    else:
                        temp_str = f"{temp}°C"
                    
                    Label(temp_frame,
                         text=temp_str,
                         font=("Helvetica", 12, "bold"),  # Smaller font
                         bg=COLORS['card_bg'],
                         fg=COLORS['text_primary']).pack()
                except Exception as e:
                    print(f"Error displaying temperature: {e}")
                
                # Weather description
                desc_frame = Frame(day_frame, bg=COLORS['card_bg'])
                desc_frame.pack(fill=X, pady=(0, 0))  # Removed vertical padding
                
                try:
                    desc = day.get('weather', '').title()
                    Label(desc_frame,
                         text=desc,
                         font=("Helvetica", 7),  # Smaller font
                         bg=COLORS['card_bg'],
                         fg=COLORS['text_secondary'],
                         wraplength=day_width-10,  # Reduced wraplength
                         justify='center').pack()
                except Exception as e:
                    print(f"Error displaying weather description: {e}")
                
            except Exception as e:
                print(f"Error creating forecast day {i}: {e}")
                continue
        
        # Update the canvas scroll region
        canvas.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        
        # Only show scrollbar if content is wider than canvas
        if canvas.bbox("all")[2] > canvas.winfo_width():
            x_scrollbar.pack(fill=X, pady=(0, 5))
        
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

        # Get current weather data
        data = get_weather(city)
        if not data:
            messagebox.showerror("Error", "Could not retrieve weather data")
            return

        # Get forecast data
        forecast_data = get_forecast(city)
        if not forecast_data:
            print("Warning: Could not retrieve forecast data")
        
        # Convert temperatures
        temp, temp_unit = convert_temp(data['main']['temp'])
        feels_like, _ = convert_temp(data['main']['feels_like'])
        temp_min, _ = convert_temp(data['main']['temp_min'])
        temp_max, _ = convert_temp(data['main']['temp_max'])

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
                icon_label.image = icon_photo  # Keep a reference
                icon_label.pack(side=RIGHT, padx=10)
        except Exception as e:
            print(f"Error loading weather icon: {e}")
        
        # Weather details
        weather_desc = data["weather"][0]["description"].title()
        desc_label = Label(city_date_frame, 
                         text=weather_desc, 
                         font=("Helvetica", 14),
                         bg=COLORS['surface'],
                         fg=COLORS['text_primary'])
        desc_label.pack(anchor='w', pady=(0, 10))
        
        # Temperature display
        temp_frame = Frame(city_date_frame, bg=COLORS['surface'])
        temp_frame.pack(anchor='w')
        
        temp_label = Label(temp_frame, 
                         text=f"{temp}°{temp_unit}", 
                         font=("Helvetica", 48, "bold"),
                         bg=COLORS['surface'],
                         fg=COLORS['primary'])
        temp_label.pack(side=LEFT)
        
        # Additional weather info
        details_frame = Frame(city_date_frame, bg=COLORS['surface'])
        details_frame.pack(fill=X, pady=(10, 0))
        
        # Feels like
        feels_frame = Frame(details_frame, bg=COLORS['surface'])
        feels_frame.pack(side=LEFT, padx=(0, 20))
        Label(feels_frame, 
             text="Feels like", 
             font=("Helvetica", 10),
             bg=COLORS['surface'],
             fg=COLORS['text_secondary']).pack(anchor='w')
        Label(feels_frame, 
             text=f"{feels_like}°{temp_unit}", 
             font=("Helvetica", 12, "bold"),
             bg=COLORS['surface'],
             fg=COLORS['text_primary']).pack(anchor='w')
        
        # Min/Max temp
        minmax_frame = Frame(details_frame, bg=COLORS['surface'])
        minmax_frame.pack(side=LEFT, padx=20)
        Label(minmax_frame, 
             text="Min/Max", 
             font=("Helvetica", 10),
             bg=COLORS['surface'],
             fg=COLORS['text_secondary']).pack(anchor='w')
        Label(minmax_frame, 
             text=f"{temp_min}°{temp_unit} / {temp_max}°{temp_unit}", 
             font=("Helvetica", 12, "bold"),
             bg=COLORS['surface'],
             fg=COLORS['text_primary']).pack(anchor='w')
        
        # Add forecast section if we have forecast data
        if forecast_data:
            forecast_frame = Frame(main_container, bg=COLORS['background'])
            forecast_frame.pack(fill=BOTH, expand=True)
            display_forecast_gui(forecast_data, forecast_frame)
        
    except Exception as e:
        print(f"Error in show_weather: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error", f"Failed to fetch weather data: {e}")

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
        auto_detect_btn.config(state=tk.NORMAL, text="📍 Auto Detect")

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

# Theme toggle button
theme_btn = Button(header_frame, 
                 text="🌞",  # Sun emoji for light theme
                 command=toggle_theme,
                 bg=COLORS['toggle_bg'],
                 fg=COLORS['toggle_fg'],
                 activebackground=COLORS['primary_dark'],
                 activeforeground='white',
                 font=("Segoe UI Emoji", 14),
                 padx=10,
                 pady=2,
                 bd=0,
                 relief=FLAT)
theme_btn.pack(side=RIGHT, padx=5)

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

# Unit toggle button
unit_toggle_btn = Button(search_container, 
                       text="🌡️ °F" if use_celsius else "🌡️ °C",  
                       command=toggle_units,
                       bg=COLORS['primary_light'], 
                       fg='white',
                       activebackground=COLORS['primary_dark'],
                       activeforeground='white',
                       font=("Segoe UI Emoji", 12, "bold"),
                       width=5,  
                       bd=0,
                       relief=FLAT)
unit_toggle_btn.pack(side=RIGHT, padx=(10, 0))

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
                   text="🌤️ Get Weather",  
                   command=show_weather,
                   bg=COLORS['primary'], 
                   fg='white', 
                   activebackground=COLORS['primary_dark'],
                   activeforeground='white',
                   font=("Segoe UI Emoji", 12, "bold"),
                   padx=20, 
                   pady=6, 
                   bd=0,
                   relief=FLAT)
search_btn.pack(side=LEFT, padx=(0, 10))

auto_detect_btn = Button(button_frame, 
                        text="📍 Auto Detect",  
                        command=auto_detect_location,
                        bg=COLORS['accent'], 
                        fg='white',
                        activebackground=COLORS['primary_dark'],
                        activeforeground='white',
                        font=("Segoe UI Emoji", 12, "bold"),
                        padx=20, 
                        pady=6, 
                        bd=0,
                        relief=FLAT)
auto_detect_btn.pack(side=LEFT)

# Weather info container
weather_container = Frame(main_frame, bg=COLORS['background'])
weather_container.pack(fill=BOTH, expand=True, pady=(10, 0))

root.mainloop()
