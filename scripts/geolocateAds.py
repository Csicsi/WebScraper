import sqlite3
import requests
import time
from config import GOOGLE_API_KEY

DB_NAME = "../data/scraped_ads.db"
GOOGLE_MAPS_API_KEY = GOOGLE_API_KEY

api_call_count = 0

def get_ads_without_coordinates():
    """Fetch ads that do not have latitude and longitude stored."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, zip_code, city, region FROM ads WHERE latitude IS NULL OR longitude IS NULL")
    ads = cursor.fetchall()
    conn.close()
    return ads

def check_location_cache(zip_code, city):
    """Check if coordinates for the given address already exist in the cache."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT latitude, longitude FROM location_cache
        WHERE zip_code = ? AND city = ?
    """, (zip_code, city))
    result = cursor.fetchone()
    conn.close()
    return result  # Returns (latitude, longitude) if found, else None

def add_to_location_cache(zip_code, city, latitude, longitude):
    """Store a new geocoded location in the cache."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO location_cache (zip_code, city, latitude, longitude)
        VALUES (?, ?, ?, ?)
    """, (zip_code, city, latitude, longitude))
    conn.commit()
    conn.close()

def geocode_address(zip_code, city, region):
    """Get latitude and longitude from cache or Google Maps API if not found."""
    global api_call_count

    if not zip_code and not city:
        return None, None  # Cannot geocode without enough info

    # Check location cache first
    cached_coords = check_location_cache(zip_code, city)
    if cached_coords:
        print(f"✅ Using cached coordinates: {cached_coords[0]}, {cached_coords[1]}")
        return cached_coords  # Return cached coordinates

    # If not in cache, make an API call
    address_parts = [zip_code, city, region]
    address = ", ".join(filter(None, address_parts))  # Join non-empty parts
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_MAPS_API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        if data["status"] == "OK":
            location = data["results"][0]["geometry"]["location"]
            latitude, longitude = location["lat"], location["lng"]

            # Add new result to cache
            add_to_location_cache(zip_code, city, latitude, longitude)

            api_call_count += 1  # Increment API call counter
            print(f"🌍 Geocoded (API Call #{api_call_count}): {address} → {latitude}, {longitude}")
            return latitude, longitude
        else:
            print(f"⚠️ Geocoding failed for: {address} ({data['status']})")
            return None, None
    except Exception as e:
        print(f"❌ Error during geocoding: {e}")
        return None, None

def update_ad_coordinates(ad_id, latitude, longitude):
    """Update the database with latitude and longitude for an ad."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE ads SET latitude = ?, longitude = ? WHERE id = ?", (latitude, longitude, ad_id))
    conn.commit()
    conn.close()

def geolocate_ads():
    """Fetch ads without coordinates, geocode them, and update the database."""
    ads = get_ads_without_coordinates()

    if not ads:
        print("✅ All ads are already geolocated.")
        return

    for ad_id, zip_code, city, region in ads:
        print(f"📍 Geolocating: {zip_code}, {city}, {region}...")

        latitude, longitude = geocode_address(zip_code, city, region)

        if latitude is not None and longitude is not None:
            update_ad_coordinates(ad_id, latitude, longitude)
            print(f"✅ Updated ID {ad_id}: {latitude}, {longitude}")
        else:
            print(f"⚠️ Could not determine location for ID {ad_id}")

        time.sleep(1)  # Prevent exceeding API request limits

    print(f"\n🌍 API Calls Made: {api_call_count}")  # Show API call count at the end
