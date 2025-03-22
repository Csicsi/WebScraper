import sqlite3
import re

# Connect to the database
db_path = "scraped_ads.db"  # Update if necessary
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if columns exist
cursor.execute("PRAGMA table_info(ads);")
columns = [col[1] for col in cursor.fetchall()]
if "price" not in columns or "size" not in columns:
    print("Error: Table 'ads' does not have the required columns 'price' and 'size'.")
    conn.close()
    exit()

# Function to clean and convert price
def clean_price(price):
    if not isinstance(price, str):
        return None

    # Remove "EUR ", spaces, and non-breaking spaces
    cleaned_price = price.replace("EUR", "").replace(" ", "").strip()

    # Handle European formatting (dot as thousand separator, comma as decimal separator)
    cleaned_price = cleaned_price.replace(".", "").replace(",", ".")

    # Extract numeric value
    match = re.search(r"(\d+(\.\d+)?)", cleaned_price)
    if match:
        return int(float(match.group(1)))  # Convert to integer
    else:
        print(f"Skipping invalid price: {price}")
        return None

# Function to clean and convert size
def clean_size(size):
    if not isinstance(size, str):
        return None

    # Remove " m²" and spaces
    cleaned_size = size.replace(" m²", "").replace(",", ".").strip()

    try:
        return float(cleaned_size)
    except ValueError:
        print(f"Skipping invalid size: {size}")
        return None

# Fetch and update price values
cursor.execute("SELECT id, price FROM ads")
price_updates = []
for ad_id, price in cursor.fetchall():
    new_price = clean_price(price)
    if new_price is not None:
        price_updates.append((new_price, ad_id))

if price_updates:
    cursor.executemany("UPDATE ads SET price = ? WHERE id = ?", price_updates)

# Fetch and update size values
cursor.execute("SELECT id, size FROM ads")
size_updates = []
for ad_id, size in cursor.fetchall():
    new_size = clean_size(size)
    if new_size is not None:
        size_updates.append((new_size, ad_id))

if size_updates:
    cursor.executemany("UPDATE ads SET size = ? WHERE id = ?", size_updates)

# Commit changes and close connection
conn.commit()
conn.close()

print("Database cleaned successfully!")
