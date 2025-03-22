import sqlite3
import pandas as pd
import json
import re

# Database setup
DATABASE_FILE = "../data/oebb_travel_times.db"
TABLE_NAME = "travel_times"
JSON_OUTPUT = "../data/travel_times.json"

# Function to clean station names from URLs
def extract_station_name(station):
    match = re.search(r"https://bahnhof\.oebb\.at/de/[^/]+/(.+)", station)
    if match:
        # Extract the last part of the URL (station name)
        station_name = match.group(1)
        # Replace hyphens with spaces and format correctly
        formatted_name = " ".join(word.capitalize() for word in station_name.split("-"))
        return formatted_name
    return station  # Return original if no match

# Load travel times from database
def load_travel_times():
    conn = sqlite3.connect(DATABASE_FILE)
    query = f"""
        SELECT station, latitude, longitude, destination, shortest_travel_time
        FROM {TABLE_NAME}
        WHERE shortest_travel_time > 0
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Convert data to JSON format
def save_json(df):
    data = {}

    for _, row in df.iterrows():
        original_station = row["station"]  # Keep original name
        extracted_station = extract_station_name(original_station)  # Extract clean name

        if extracted_station not in data:
            data[extracted_station] = {
                "original_name": original_station,  # Store original name for comparison
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "travel_times": {}
            }

        data[extracted_station]["travel_times"][row["destination"]] = row["shortest_travel_time"]

    with open(JSON_OUTPUT, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"✅ Travel time data saved as {JSON_OUTPUT}")

if __name__ == "__main__":
    df = load_travel_times()

    if df.empty:
        print("⚠️ No travel time data found.")
    else:
        save_json(df)
