import time
import sqlite3
import googlemaps
from config import GOOGLE_API_KEY

API_KEY = GOOGLE_API_KEY
gmaps = googlemaps.Client(key=API_KEY)

# New SQLite DB file
DB_FILE = "../data/oebb_stations_geo.db"
FAILED_FILE = "../data/failed_geocoding.txt"

def init_db():
    """Create a new database table to store URLs, addresses, and GPS coordinates."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stations_geo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            address TEXT,
            latitude REAL,
            longitude REAL
        )
    """)
    conn.commit()
    conn.close()

def address_exists(url):
    """Check if a station URL is already in the new database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stations_geo WHERE url = ?", (url,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_coordinates(address):
    """Fetch latitude and longitude using Google Maps API."""
    try:
        geocode_result = gmaps.geocode(address)
        if geocode_result:
            location = geocode_result[0]["geometry"]["location"]
            return location["lat"], location["lng"]
    except Exception as e:
        print(f"⚠️ Google Maps API failed for: {address} | Error: {e}")
    return None, None

def save_to_db(url, address, latitude, longitude):
    """Insert station data into the new database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO stations_geo (url, address, latitude, longitude)
        VALUES (?, ?, ?, ?)
    """, (url, address, latitude, longitude))
    conn.commit()
    conn.close()

def save_failed(url, address):
    """Save failed addresses to a text file for later reprocessing."""
    with open(FAILED_FILE, "a", encoding="utf-8") as fail_file:
        fail_file.write(f"{url}|{address}\n")

# Initialize the new database
init_db()

# Read existing database with full addresses
old_db = "../data/oebb_stations.db"
conn_old = sqlite3.connect(old_db)
cursor_old = conn_old.cursor()
cursor_old.execute("SELECT url, postal_code FROM stations")  # Full address is in postal_code

stations = cursor_old.fetchall()
conn_old.close()

# Process and store each station
for url, address in stations:
    if address_exists(url):
        print(f"⏩ Skipping (already in DB): {url}")
        continue

    print(f"🌍 Fetching coordinates for: {address}")

    lat, lon = get_coordinates(address)

    if lat and lon:
        save_to_db(url, address, lat, lon)
        print(f"✅ Saved: {address} → ({lat}, {lon})")
    else:
        print(f"❌ Failed to get coordinates: {address}")
        save_failed(url, address)  # Save to failed list

    time.sleep(1)  # Avoid hitting API rate limits

print(f"✅ Process complete. Data saved in '{DB_FILE}'.")
print(f"❌ Failed stations logged in '{FAILED_FILE}'.")
