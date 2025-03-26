import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "../data/scraped_ads.db")
DB_NAME = os.path.abspath(DB_NAME)  # optional, resolves full path

def create_table():
    """Ensures the database table exists without dropping existing data."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            price INTEGER,
            size REAL,
            price_per_m2 REAL,
            zip_code TEXT,
            city TEXT,
            region TEXT,
            price_info TEXT,
            energy_certificate TEXT,
            attributes TEXT,
            date_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def insert_ad(url, title, price, size, price_per_m2, zip_code, city, region, price_info, energy_certificate, attributes):
    """Inserts a new ad into the database if it doesn't already exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO ads (url, title, price, size, price_per_m2, zip_code, city, region, price_info, energy_certificate, attributes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            url, title, price, size, price_per_m2, zip_code, city, region,
            json.dumps(price_info, ensure_ascii=False),
            json.dumps(energy_certificate, ensure_ascii=False),
            json.dumps(attributes, ensure_ascii=False)
        ))

        conn.commit()
        print(f"✅ Added to database: {title} ({price}€) | {city}, {region}")

    except sqlite3.IntegrityError:
        print(f"⚠️ Skipped (Already in DB): {title}")

    conn.close()

# Ensure the table is created before inserting ads
create_table()
