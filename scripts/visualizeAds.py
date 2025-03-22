import sqlite3
import pandas as pd
import json
import math
import time

# Database setup
DATABASE_FILE = "../data/scraped_ads.db"
TABLE_ADS = "ads"
DATABASE_STATIONS = "../data/oebb_travel_times.db"
TABLE_STATIONS = "travel_times"
JSON_OUTPUT = "../data/real_estate_ads.json"

# Haversine formula to calculate straight-line distance (in meters)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# Load train stations from database
def load_train_stations():
    print("📡 Fetching train station data...")
    conn = sqlite3.connect(DATABASE_STATIONS)
    query = f"SELECT station, latitude, longitude FROM {TABLE_STATIONS}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    print(f"✅ Loaded {len(df)} train stations.")
    return df

# Load real estate ads from database and compute nearest station
def load_real_estate_ads(stations):
    print("🏠 Fetching real estate ads...")
    conn = sqlite3.connect(DATABASE_FILE)
    query = f"""
        SELECT url, title, price, size, zip_code, city, region, latitude, longitude
        FROM {TABLE_ADS}
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    print(f"✅ Loaded {len(df)} real estate ads.")

    # Compute nearest station for each ad
    ads = []
    total_ads = len(df)
    start_time = time.time()

    for i, row in df.iterrows():
        min_distance = float("inf")
        nearest_station = None

        for _, station in stations.iterrows():
            distance = haversine(row["latitude"], row["longitude"], station["latitude"], station["longitude"])
            if distance < min_distance:
                min_distance = distance
                nearest_station = station["station"]

        ads.append({
            "url": row["url"],
            "title": row["title"],
            "price": row["price"],
            "size": row["size"],
            "zip_code": row["zip_code"],
            "city": row["city"],
            "region": row["region"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "nearest_station": nearest_station,
            "distance_to_station": round(min_distance, 2)  # Store precomputed distance
        })

        # Print progress every 100 ads
        if (i + 1) % 100 == 0 or (i + 1) == total_ads:
            elapsed_time = time.time() - start_time
            print(f"⏳ Processed {i + 1}/{total_ads} ads ({elapsed_time:.2f} sec)")

    print("✅ Finished processing all ads.")
    return ads

# Save data to JSON
def save_json(ads):
    print("💾 Saving data to JSON file...")
    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(ads, f, indent=4, ensure_ascii=False)
    print(f"✅ Real estate ads saved with precomputed distances in {JSON_OUTPUT}")

def process_data():
    print("🚀 Starting data processing...")
    stations = load_train_stations()
    ads = load_real_estate_ads(stations)

    if not ads:
        print("⚠️ No real estate ads found.")
    else:
        save_json(ads)

    print("🎉 Processing complete!")
