import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from database import insert_ad  # Using existing insert_ad method from Willhaben DB

# Setup Selenium WebDriver
service = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(service=service, options=options)

# Open RE/MAX search page
driver.get("https://www.remax.at/de/immobilien/immobilien-suchen")

# Wait for manual filtering
print("🔹 The browser is open. Please set your filters manually.")
input("🔸 Press Enter to continue scraping once filters are set...")

def scrape_ad(url):
    """Extracts ZIP, City, Size, and Price, then saves to DB one by one"""

    # Open ad in a new tab
    driver.execute_script(f"window.open('{url}', '_blank');")
    driver.switch_to.window(driver.window_handles[1])  # Switch to the new tab
    time.sleep(2)  # Allow page to load

    try:
        # Locate the address container
        zip_code, city = "N/A", "N/A"
        try:
            address_container = driver.find_element(By.CLASS_NAME, "immodetail-address")
            location_element = address_container.find_element(By.CSS_SELECTOR, "h2.id-infobox")
            location_text = location_element.text.strip()
            print(f"📍 Found Location: {location_text}")

            # Split ZIP and City
            parts = location_text.split(" - ")
            if len(parts) == 2:
                zip_code, city = parts
            else:
                city = location_text  # If no ZIP, store full location as city

            print(f"   🏙️ ZIP: {zip_code}, City: {city}")

        except:
            print("⚠️ Location not found in immodetail-address")

        # Extract details dynamically
        size, price = "N/A", "N/A"
        try:
            info_table = driver.find_element(By.CLASS_NAME, "immodetail-infotable")
            rows = info_table.find_elements(By.TAG_NAME, "tr")

            print(f"🔍 Found {len(rows)} rows in immodetail-infotable:")

            for i, row in enumerate(rows):
                columns = row.find_elements(By.TAG_NAME, "td")
                column_values = [col.text.strip() for col in columns]

                print(f"  🔹 Row {i + 1}: {column_values}")  # Debug print

                if len(column_values) == 3:  # If row contains exactly 3 columns
                    size, _, price = column_values  # Second value is rooms, we ignore it
                    print(f"    📏 Found Size: {size}")
                    print(f"    💰 Found Price: {price}")
                    break  # Stop after finding the first valid row

        except Exception as e:
            print(f"⚠️ Error extracting from immodetail-infotable: {e}")

        # Insert ad into DB one by one
        print(f"💾 Inserting into DB: {url}")
        insert_ad(
            url,
            "RE/MAX Listing",
            price,
            size,
            "N/A",  # Not available from RE/MAX, can be calculated later
            zip_code,
            city,
            "N/A",  # RE/MAX does not provide a clear region
            {},
            {},  # No attributes available
            {}
        )

    except Exception as e:
        print(f"⚠️ Error scraping {url}: {e}")

    # Close the tab and return to main page
    driver.close()
    driver.switch_to.window(driver.window_handles[0])  # Switch back to main tab

try:
    while True:  # Loop through pages until there is no 'next' button
        time.sleep(2)  # Wait for page load

        # Find all ad links and store only unique URLs
        ads = driver.find_elements(By.CSS_SELECTOR, "a.immobox-hoch--body__title")
        ad_urls = {ad.get_attribute("href") for ad in ads if ad.get_attribute("href")}  # Use set to remove duplicates

        # Scrape and insert each ad one by one
        for url in sorted(ad_urls):  # Sorting for consistent order
            scrape_ad(url)

        # Find and click the "Next" button in the main tab
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "a.next")
            driver.execute_script("arguments[0].click();", next_button)  # JavaScript click to avoid issues
            print("\n➡️ Moving to the next page...\n")
            time.sleep(2)  # Wait for new page to load
        except:
            print("\n🚀 No more pages. Scraping complete.")
            break

except Exception as e:
    print(f"❌ Error during scraping: {e}")

finally:
    print("\n✅ Scraping finished. Closing browser...")
    driver.quit()
