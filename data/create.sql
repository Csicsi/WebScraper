INSERT OR IGNORE INTO location_cache (zip_code, city, latitude, longitude)
SELECT DISTINCT zip_code, city, latitude, longitude
FROM ads
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
