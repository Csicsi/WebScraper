import time
import sqlite3
import googlemaps
from config import GOOGLE_API_KEY

API_KEY = GOOGLE_API_KEY
gmaps = googlemaps.Client(key=API_KEY)

# New SQLite DB file
DB_FILE = "../data/oebb_stations_geo.db"
FAILED_FILE = "../data/failed_geocoding.txt"

# List of Badner Bahn stations
badner_bahn_stations = [
    "Wien Oper Karlsplatz", "Wien Resselgasse", "Wien Paulanergasse",
    "Wien Johann-Strauss-Gasse", "Wien Kliebergasse", "Wien Eichenstraße",
    "Wien Murlingengasse", "Wien Wolfganggasse", "Wien Steinbauergasse",
    "Wien Aßmayergasse", "Wien Meidling", "Wien Dörfelstraße",
    "Wien Schedifkaplatz", "Wien Schönbrunner Allee", "Wien Schöpfwerk",
    "Wien Gutheil-Schoder-Gasse", "Wien Inzersdorf", "Vösendorf-Siebenhirten",
    "Vösendorf", "Maria Enzersdorf Südstadt", "Wiener Neudorf",
    "Griesfeld", "Guntramsdorf Lokalbahn", "Neu-Guntramsdorf",
    "Pfaffstätten Rennplatz", "Baden Viadukt", "Baden Josefsplatz"
]

def init_db():
    """Create a new database table to store Badner Bahn stations."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS badner_bahn (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station TEXT UNIQUE,
            latitude REAL,
            longitude REAL
        )
    """)
    conn.commit()
    conn.close()

def station_exists(station):
    """Check if a station is already in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM badner_bahn WHERE station = ?", (station,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_coordinates(station):
    """Fetch latitude and longitude using Google Maps API."""
    try:
        geocode_result = gmaps.geocode(station + ", Austria")
        if geocode_result:
            location = geocode_result[0]["geometry"]["location"]
            return location["lat"], location["lng"]
    except Exception as e:
        print(f"⚠️ Google Maps API failed for: {station} | Error: {e}")
    return None, None

def save_to_db(station, latitude, longitude):
    """Insert station data into the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO badner_bahn (station, latitude, longitude)
        VALUES (?, ?, ?)
    """, (station, latitude, longitude))
    conn.commit()
    conn.close()

def save_failed(station):
    """Save failed stations to a text file for later reprocessing."""
    with open(FAILED_FILE, "a", encoding="utf-8") as fail_file:
        fail_file.write(f"{station}\n")

# Initialize the database
init_db()

# Process each station
for station in badner_bahn_stations:
    if station_exists(station):
        print(f"⏩ Skipping (already in DB): {station}")
        continue

    print(f"🌍 Fetching coordinates for: {station}")

    lat, lon = get_coordinates(station)

    if lat and lon:
        save_to_db(station, lat, lon)
        print(f"✅ Saved: {station} → ({lat}, {lon})")
    else:
        print(f"❌ Failed to get coordinates: {station}")
        save_failed(station)  # Save to failed list

    time.sleep(1)  # Avoid hitting API rate limits

print(f"✅ Process complete. Data saved in '{DB_FILE}'.")
print(f"❌ Failed stations logged in '{FAILED_FILE}'.")
