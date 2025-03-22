import time
import random
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from willhabenScraper import scrape_willhaben_details, url_exists_in_db
from database import create_table, insert_ad

def accept_cookies(driver):
    try:
        cookie_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
        )
        cookie_button.click()
        print("✅ Accepted Cookies")
        time.sleep(2)
    except Exception as e:
        print("⚠️ No cookie popup found (or already closed)")

def slow_scroll(driver, max_scrolls=10):
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(max_scrolls):
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(random.uniform(1.2, 2.5))
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    print("✅ Scrolling completed, all ads should be visible.")

def get_all_ad_urls(driver):
    slow_scroll(driver)
    try:
        ad_elements = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[data-testid^='search-result-entry-header']"))
        )
        ad_links = [ad.get_attribute("href") for ad in ad_elements]
        ad_urls = [f"https://www.willhaben.at{link}" if link.startswith("/") else link for link in ad_links]
        print(f"🔍 Found {len(ad_urls)} ads on this page.")
        return ad_urls
    except Exception as e:
        print("❌ No ads found.")
        return []

def next_page_url(url, page_number):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_params["page"] = [str(page_number)]
    new_query = urlencode(query_params, doseq=True)
    new_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, new_query, parsed_url.fragment))
    return new_url

def scrape_all_pages(search_url, stop_on_seen=False):
    create_table()
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    page = 1
    try:
        while True:
            print(f"📄 Scraping Page {page}...")
            page_url = next_page_url(search_url, page)
            driver.get(page_url)
            accept_cookies(driver)
            ad_urls = get_all_ad_urls(driver)
            if not ad_urls:
                print("🚫 No more ads found. Stopping pagination.")
                break
            for i, ad_url in enumerate(ad_urls):
                # Check the database instead of a local seen set
                if stop_on_seen and url_exists_in_db(ad_url):
                    print(f"⚠️ Already seen ad encountered in DB: {ad_url}")
                    print("⏹ Stopping further scraping as per user preference.")
                    return
                print(f"📄 Scraping ad {i + 1}/{len(ad_urls)}: {ad_url}")
                ad_data = scrape_willhaben_details(driver, ad_url)
                if ad_data is None or ad_data.get("Price (€)") is None or ad_data.get("Size (m²)") is None:
                    print(f"⚠️ Skipping ad (missing price/size): {ad_url}")
                    continue
                location = ad_data["Location"]
                insert_ad(
                    ad_data["URL"],
                    ad_data["Title"],
                    ad_data["Price (€)"],
                    ad_data["Size (m²)"],
                    ad_data["Price per m² (€)"],
                    location["ZIP Code"],
                    location["City"],
                    location["Region"],
                    ad_data["Price Information"],
                    ad_data["Energy Certificate"],
                    ad_data["Attributes"]
                )
            page += 1
    finally:
        driver.quit()
