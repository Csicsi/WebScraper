import time
import sqlite3
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Initialize SQLite database
DB_FILE = "../data/oebb_stations.db"

def init_db():
    """Create the database table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            postal_code TEXT,
            street TEXT,
            state TEXT,
            url TEXT UNIQUE
        )
    """)
    conn.commit()
    conn.close()

def address_exists(url):
    """Check if a station URL is already in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stations WHERE url = ?", (url,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def save_to_db(postal_code, street, state, url):
    """Insert station data into the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO stations (postal_code, street, state, url)
        VALUES (?, ?, ?, ?)
    """, (postal_code, street, state, url))
    conn.commit()
    conn.close()

# Set up Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Read verified URLs from file
with open("../data/oebb_station_urls.txt", "r", encoding="utf-8") as file:
    station_urls = [line.strip() for line in file.readlines() if line.strip()]

stations_data = []
failed_stations = []

# Initialize database
init_db()

# Scrape each station if not already in the database
for url in station_urls:
    if address_exists(url):
        print(f"⏩ Skipping (already in DB): {url}")
        continue  # Skip already saved stations

    driver.get(url)

    try:
        # Wait until <p> elements are present
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "p")))

        # Extract all <p> elements
        p_elements = driver.find_elements(By.TAG_NAME, "p")
        address_lines = [p.text.strip() for p in p_elements if p.text.strip()]

        # Check if we have at least 3 lines for postal code, street, and state
        if len(address_lines) >= 3:
            postal_code = address_lines[0]
            street = address_lines[1]
            state = address_lines[2]

            save_to_db(postal_code, street, state, url)
            print(f"✅ Scraped and saved: {url}")

        else:
            raise ValueError("Address format incorrect")

    except Exception as e:
        print(f"❌ Failed: {url} | Error: {str(e)}")
        failed_stations.append(url)

# Close WebDriver
driver.quit()

# Save failed stations to a separate file
with open("../data/failed_stations.txt", "w", encoding="utf-8") as fail_file:
    for fail in failed_stations:
        fail_file.write(f"{fail}\n")

print(f"✅ Scraping complete. Data saved to '{DB_FILE}'.")
print(f"❌ Failed stations logged in 'failed_stations.txt'.")
