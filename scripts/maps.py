import time
import sqlite3
import googlemaps
from datetime import datetime, timedelta
from config import GOOGLE_API_KEY

API_KEY = GOOGLE_API_KEY
gmaps = googlemaps.Client(key=API_KEY)

# New SQLite DB file for travel times
DB_FILE = "../data/oebb_travel_times.db"
FAILED_FILE = "../data/failed_travel_times.txt"

DESTINATIONS = {
	"Schimetta": (48.18453801245323, 16.33267402432996),
	"Sopron": (47.677941640681716, 16.586646100139717),
	"Gloggnitz": (47.677495754300445, 15.946853680770328)
}


# Define time range (09:00 - 18:00, every 30 minutes)
START_TIME = "09:00"
END_TIME = "18:00"
INTERVAL_MINUTES = 30

def init_db():
    """Create a new database table to store travel times."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS travel_times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station TEXT,
            destination TEXT,
            shortest_travel_time INTEGER,  -- In minutes
            departure_time TEXT,
            latitude REAL,
            longitude REAL
        )
    """)
    conn.commit()
    conn.close()

def station_exists(station, destination):
    """Check if a travel time entry is already in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM travel_times WHERE station = ? AND destination = ?
    """, (station, destination))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_travel_time(origin, destination_coords, departure_time):
    """Fetch public transport travel time from Google Maps API."""
    try:
        directions = gmaps.directions(
            origin, f"{destination_coords[0]},{destination_coords[1]}",
            mode="transit",
            departure_time=departure_time,
            transit_routing_preference="fewer_transfers"
        )
        if directions:
            return directions[0]["legs"][0]["duration"]["value"] // 60  # Convert seconds to minutes
    except Exception as e:
        print(f"⚠️ API failed for {origin} → {destination_coords} | Error: {e}")
    return None

def save_to_db(station, destination, travel_time, departure_time, latitude, longitude):
    """Insert the shortest travel time into the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO travel_times (station, destination, shortest_travel_time, departure_time, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (station, destination, travel_time, departure_time, latitude, longitude))
    conn.commit()
    conn.close()

def save_failed(station, destination, latitude, longitude):
    """Save failed attempts to a separate file for retrying later."""
    with open(FAILED_FILE, "a", encoding="utf-8") as fail_file:
        fail_file.write(f"{station}|{destination}|{latitude}|{longitude}\n")

# Initialize the database
init_db()

# Read all stations (ÖBB + Badner Bahn) from `oebb_stations_geo.db`
conn_geo = sqlite3.connect("../data/oebb_stations_geo.db")
cursor_geo = conn_geo.cursor()

# Fetch all stations from both tables
cursor_geo.execute("SELECT url, latitude, longitude FROM stations_geo")
oebb_stations = cursor_geo.fetchall()

cursor_geo.execute("SELECT station, latitude, longitude FROM badner_bahn")
badner_stations = cursor_geo.fetchall()

conn_geo.close()

all_stations = oebb_stations + badner_stations  # Merge both lists

# Process each station and calculate the shortest travel time
for station, lat, lon in all_stations:
    for dest_name, dest_coords in DESTINATIONS.items():
        if station_exists(station, dest_name):
            print(f"⏩ Skipping (already in DB): {station} → {dest_name}")
            continue

        print(f"🚆 Calculating travel time: {station} → {dest_name}")

        # Generate departure times (every 30 minutes from 09:00 to 18:00)
        date_today = datetime.today()
        start_dt = datetime.strptime(f"{date_today.date()} {START_TIME}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{date_today.date()} {END_TIME}", "%Y-%m-%d %H:%M")
        current_time = start_dt

        shortest_time = None
        best_departure = None

        while current_time <= end_dt:
            travel_time = get_travel_time(f"{lat},{lon}", dest_coords, current_time)

            if travel_time is not None:
                if shortest_time is None or travel_time < shortest_time:
                    shortest_time = travel_time
                    best_departure = current_time.strftime("%H:%M")

            current_time += timedelta(minutes=INTERVAL_MINUTES)  # Increment by 30 minutes

        if shortest_time is not None:
            save_to_db(station, dest_name, shortest_time, best_departure, lat, lon)
            print(f"✅ Saved: {station} → {dest_name} ({shortest_time} min, best at {best_departure})")
        else:
            print(f"❌ No valid travel times found for {station} → {dest_name}")
            save_failed(station, dest_name, lat, lon)  # Save to failed list

    time.sleep(1)  # Avoid hitting API rate limits

print(f"✅ Process complete. Data saved in '{DB_FILE}'.")
print(f"❌ Failed stations logged in '{FAILED_FILE}'.")
