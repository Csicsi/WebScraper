# 🏠 Real Estate Ad Scraper

This is a personal side project built to assist with my flat search near Vienna. It scrapes real estate listings, stores them in an SQL database, exports them to JSON, and displays them on a map-based frontend.

It’s not fully connected or automated yet, but it gives me what I need: **a map view of all listings with nearby train stations and travel times to key locations**.

---

## 🌟 Key Advantage

The biggest strength of this tool is **visualizing listings on a map** — complete with:

- Nearby **train stations**
- Estimated **travel times** (by public transport) to locations that matter to us (e.g., work, family, etc.)

It makes comparing flats much easier than scrolling through random search results.

---

## 🔧 Current Features

- Scrapes listings from real estate sites (e.g., Willhaben, Remax)
- Saves data to an **SQL database**
- Converts listings to **JSON** for use in a website
- Manually run in steps (not fully connected yet)
- Shows listings on a **map with POIs and travel times**

---

## 🛠️ How It Works (Currently)

Scripts are run **manually**, in order:

1. Scrape data  
2. Save to database  
3. Export to JSON  
4. Load the frontend to view listings on a map  

---

## ⚙️ Tech Stack

- **Backend:** Python (Selenium)
- **Database:** SQLite
- **Frontend:** Static site with map view (HTML/CSS/JS)
- **Optional:** Google Maps API for travel time calculations

---

## ⚠️ Still Missing

- Automation/scheduling  
- Alerts or ranking logic  
- Connected pipeline (currently modular and run step-by-step)

---

## 💬 Why I Made This

I was tired of refreshing listing websites and guessing commute times. This tool gives me a clearer picture of which places are actually worth visiting.

---

## 📋 Disclaimer

- Very much a personal project  
- Not polished  
- Might break if websites change layout  
- Use at your own risk
- Might violate some terms of service

---

Not pretty. Not perfect. But it works — and that’s enough for now.

Check out the [live site here](https://web-scraper2-0.vercel.app/) to see the listings on the map.

