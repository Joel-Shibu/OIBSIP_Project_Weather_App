import os
import requests

# All known weather icon codes from OpenWeatherMap
icon_codes = [
    "01d", "01n", "02d", "02n", "03d", "03n",
    "04d", "04n", "09d", "09n", "10d", "10n",
    "11d", "11n", "13d", "13n", "50d", "50n"
]

# Destination folder for icons
icon_folder = "icons"
os.makedirs(icon_folder, exist_ok=True)

# Icon base URL
base_url = "https://openweathermap.org/img/wn/{}@2x.png"

print("🔽 Downloading weather icons...")

for code in icon_codes:
    url = base_url.format(code)
    dest_path = os.path.join(icon_folder, f"{code}.png")

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise error for non-200
        with open(dest_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Downloaded: {code}")
    except Exception as e:
        print(f"❌ Failed to download {code}: {e}")

print("\n✔️ All icons processed.")
