import json
import os

from willhaben import scrape_all_pages
from remax import run_remax_scraper
from geolocateAds import geolocate_ads
from visualizeAds import process_data

URLS_FILE = "saved_urls.json"

def load_urls():
    if not os.path.exists(URLS_FILE):
        return []
    with open(URLS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_urls(urls):
    with open(URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(urls, f, indent=4)

def detect_source(url):
    if "willhaben.at" in url:
        return "willhaben"
    elif "remax.at" in url:
        return "remax"
    else:
        return None

def run_scraper(url):
    source = detect_source(url)
    if not source:
        print("❌ Unknown source. Only Willhaben and RE/MAX are supported.")
        return

    try:
        if source == "willhaben":
            scrape_all_pages(url, True)
        elif source == "remax":
            run_remax_scraper()

        geolocate_ads()
        process_data()

        print("✅ Scraping complete and JSON updated.")
    except Exception as e:
        print(f"❌ Error during scraping 2: {e}")

def list_urls():
    urls = load_urls()
    if not urls:
        print("No URLs saved.")
    else:
        print("Saved URLs:")
        for i, u in enumerate(urls):
            print(f"[{i}] {u}")

def add_url():
    new_url = input("Enter new URL: ").strip()
    if not new_url:
        print("❌ URL cannot be empty.")
        return
    urls = load_urls()
    urls.append(new_url)
    save_urls(urls)
    print("✅ URL added.")

def choose_and_run():
    urls = load_urls()
    if not urls:
        print("No URLs saved.")
        return
    list_urls()
    try:
        index = int(input("Enter the index of the URL to scrape: "))
        if 0 <= index < len(urls):
            run_scraper(urls[index])
        else:
            print("❌ Invalid index.")
    except ValueError:
        print("❌ Please enter a valid number.")

def main_menu():
    while True:
        print("\n=== Real Estate Scraper ===")
        print("1. List saved URLs")
        print("2. Add a new URL")
        print("3. Run scraper on saved URL")
        print("4. Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            list_urls()
        elif choice == "2":
            add_url()
        elif choice == "3":
            choose_and_run()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3 or 4.")

if __name__ == "__main__":
    print("🏠 Welcome to the Real Estate Scraper!")
    main_menu()
