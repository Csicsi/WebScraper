import re
import time
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

DB_NAME = "../data/scraped_ads.db"

def url_exists_in_db(url):
    """Check if a URL already exists in the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM ads WHERE url = ?", (url,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def accept_cookies(driver):
    try:
        cookie_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
        )
        cookie_button.click()
        print("✅ Accepted Cookies")
        time.sleep(1)
    except:
        print("⚠️ No cookie popup found (or already closed)")

def scrape_title(driver):
    try:
        title = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='ad-detail-header']"))
        ).text
        return title
    except:
        return "Title not found"

def scrape_price(driver):
    try:
        price_text = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='contact-box-price-box-price-value-0']"))
        ).text
        price = int(re.sub(r"[^\d]", "", price_text))
        return price
    except:
        return None

def scrape_size(driver):
    try:
        attributes = driver.find_elements(By.CSS_SELECTOR, "[data-testid='attribute-item']")
        for attribute in attributes:
            try:
                title_element = attribute.find_element(By.CSS_SELECTOR, "[data-testid='attribute-title']")
                title_text = title_element.text.strip()

                if "Wohnfläche" in title_text:
                    value_element = attribute.find_element(By.CSS_SELECTOR, "[data-testid='attribute-value']")
                    size_text = value_element.text.strip()

                    size_text = re.sub(r"[^\d,]", "", size_text).replace(",", ".")
                    size = float(size_text)
                    return size
            except:
                continue
        return None
    except:
        return None

def scrape_attributes(driver):
    attributes_dict = {}
    try:
        attributes = driver.find_elements(By.CSS_SELECTOR, "[data-testid='attribute-item']")
        for attribute in attributes:
            try:
                title_element = attribute.find_element(By.CSS_SELECTOR, "[data-testid='attribute-title']")
                value_elements = attribute.find_elements(By.CSS_SELECTOR, "[data-testid='attribute-value']")

                title_text = title_element.text.strip()
                value_texts = [value.text.strip() for value in value_elements if value.text.strip()]

                attributes_dict[title_text] = ", ".join(value_texts) if value_texts else "Ja"  # Assume "Ja" if no value given
            except:
                continue
    except:
        return {}

    return attributes_dict

def scrape_energy_certificate(driver):
    energy_data = {}
    try:
        energy_box = driver.find_element(By.CSS_SELECTOR, "[data-testid='energy-pass-box']")
        energy_labels = energy_box.find_elements(By.CSS_SELECTOR, "[data-testid^='energy-pass-attribute-label']")
        energy_values = energy_box.find_elements(By.CSS_SELECTOR, "[data-testid^='energy-pass-attribute-value']")

        for label, value in zip(energy_labels, energy_values):
            label_text = label.text.strip()
            value_text = value.text.strip()
            if label_text and value_text:
                energy_data[label_text] = value_text
    except:
        return {}

    return energy_data

def scrape_price_information(driver):
    price_info = {}
    try:
        price_box = driver.find_element(By.CSS_SELECTOR, "[data-testid='price-information-box']")
        price_labels = price_box.find_elements(By.CSS_SELECTOR, "[data-testid^='price-information-formatted-attribute-label']")
        price_values = price_box.find_elements(By.CSS_SELECTOR, "[data-testid^='price-information-formatted-attribute-value']")

        for label, value in zip(price_labels, price_values):
            label_text = label.text.strip()
            value_text = value.text.strip()
            if label_text and value_text:
                price_info[label_text] = value_text
    except:
        return {}

    return price_info

def scrape_location(driver):
    try:
        location_element = driver.find_element(By.CSS_SELECTOR, "[data-testid='object-location-address']")
        location_text = location_element.text.strip()

        # Regular expression to detect ZIP codes (assumes Austrian 4-digit format)
        zip_match = re.search(r"\b\d{4}\b", location_text)
        zip_code = zip_match.group(0) if zip_match else None

        # Extract city and region dynamically
        location_parts = location_text.split(", ")
        city = None
        region = None

        for part in location_parts:
            if zip_code and part.startswith(zip_code):
                city = part[len(zip_code):].strip()
            elif not part.isdigit():  # If not a number, assume it's a region
                region = part.strip()

        return {
            "ZIP Code": zip_code,
            "City": city if city else None,
            "Region": region if region else None
        }
    except:
        return {"ZIP Code": None, "City": None, "Region": None}

def scrape_willhaben_details(driver, url):
    """Scrape the details of a Willhaben listing only if it's not already in the database."""

    # Check if the ad already exists in the database
    if url_exists_in_db(url):
        print(f"⚠️ Skipping (Already in DB): {url}")
        return None  # Return None to indicate no scraping needed

    driver.get(url)
    accept_cookies(driver)

    title = scrape_title(driver)
    price = scrape_price(driver)
    size = scrape_size(driver)
    attributes = scrape_attributes(driver)
    energy_certificate = scrape_energy_certificate(driver)
    price_information = scrape_price_information(driver)
    location = scrape_location(driver)

    price_per_m2 = round(price / size, 2) if price and size else None

    return {
        "URL": url,
        "Title": title,
        "Price (€)": price,
        "Size (m²)": size,
        "Price per m² (€)": price_per_m2,
        "Location": location if location else {"ZIP Code": None, "City": None, "Region": None},
        "Price Information": price_information if price_information else {},
        "Energy Certificate": energy_certificate if energy_certificate else {},
        "Attributes": attributes if attributes else {}
    }
