import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from database import insert_ad

def setup_driver():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(service=service, options=options)

def scrape_remax_ads(url, driver):
    """Extracts ZIP, City, Size, and Price, then saves to DB one by one"""
    driver.execute_script(f"window.open('{url}', '_blank');")
    driver.switch_to.window(driver.window_handles[1])
    time.sleep(2)

    try:
        zip_code, city = "N/A", "N/A"
        try:
            address_container = driver.find_element(By.CLASS_NAME, "immodetail-address")
            location_element = address_container.find_element(By.CSS_SELECTOR, "h2.id-infobox")
            location_text = location_element.text.strip()
            print(f"📍 Found Location: {location_text}")
            parts = location_text.split(" - ")
            if len(parts) == 2:
                zip_code, city = parts
            else:
                city = location_text
        except:
            print("⚠️ Location not found in immodetail-address")

        size, price = "N/A", "N/A"
        try:
            info_table = driver.find_element(By.CLASS_NAME, "immodetail-infotable")
            rows = info_table.find_elements(By.TAG_NAME, "tr")
            for row in rows:
                columns = row.find_elements(By.TAG_NAME, "td")
                column_values = [col.text.strip() for col in columns]
                if len(column_values) == 3:
                    size, _, price = column_values
                    break
        except Exception as e:
            print(f"⚠️ Error extracting from immodetail-infotable: {e}")

        print(f"💾 Inserting into DB: {url}")
        insert_ad(
            url, "RE/MAX Listing", price, size, "N/A",
            zip_code, city, "N/A", {}, {}, {}
        )

    except Exception as e:
        print(f"⚠️ Error scraping {url}: {e}")

    driver.close()
    driver.switch_to.window(driver.window_handles[0])

def run_remax_scraper():
    driver = setup_driver()
    driver.get("https://www.remax.at/de/immobilien/immobilien-suchen")

    print("🔹 The browser is open. Please set your filters manually.")
    input("🔸 Press Enter to continue scraping once filters are set...")

    try:
        while True:
            time.sleep(2)
            ads = driver.find_elements(By.CSS_SELECTOR, "a.immobox-hoch--body__title")
            ad_urls = {ad.get_attribute("href") for ad in ads if ad.get_attribute("href")}
            for url in sorted(ad_urls):
                scrape_remax_ads(url, driver)

            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "a.next")
                driver.execute_script("arguments[0].click();", next_button)
                print("\n➡️ Moving to the next page...\n")
                time.sleep(2)
            except:
                print("\n🚀 No more pages. Scraping complete.")
                break

    except Exception as e:
        print(f"❌ Error during scraping: {e}")
    finally:
        print("\n✅ Scraping finished. Closing browser...")
        driver.quit()
