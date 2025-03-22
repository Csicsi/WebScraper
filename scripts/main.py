from willhaben import scrape_all_pages
from geolocateAds import geolocate_ads
from visualizeAds import process_data

def main():
    #search_url = input("Enter the search URL: ").strip()
    #choice = input("Stop at first ad that is already seen? (y/n): ").strip().lower()
    #stop_on_seen = choice.startswith("y")
    #if "willhaben" in search_url:
    #    scrape_all_pages(search_url, stop_on_seen=stop_on_seen)
    #    geolocate_ads()
    #    process_data()
    #else:
    #    print("Not a known domain. Exiting...")
    #    return
    geolocate_ads()
    process_data()
    return

if __name__ == "__main__":
    main()
