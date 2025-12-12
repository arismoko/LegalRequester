import requests
from bs4 import BeautifulSoup
import json
import time
import random
import os

BASE_URL = "https://publicrecords.netronline.com"
STATE_URL = "https://publicrecords.netronline.com/state/MN"
CACHE_FILE = 'county_urls.json'
SLUGS_FILE = 'county_slugs.json'

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
}

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=4)

def get_county_slugs():
    if os.path.exists(SLUGS_FILE):
        try:
            with open(SLUGS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass

    print(f"Fetching state page: {STATE_URL}")
    try:
        response = requests.get(STATE_URL, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            print(f"Failed to fetch state page: {response.status_code}")
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        select = soup.find('select', {'id': 'county_sel'})
        if not select:
            print("Could not find county select dropdown")
            return {}
        
        slugs = {}
        for option in select.find_all('option'):
            value = option.get('value')
            name = option.text.strip()
            if value and value != '0':
                slugs[name] = value
        
        with open(SLUGS_FILE, 'w') as f:
            json.dump(slugs, f, indent=4)
            
        return slugs
    except Exception as e:
        print(f"Error fetching slugs: {e}")
        return {}

def scrape_county_url(county_name, slug):
    url = f"{BASE_URL}/state/MN/county/{slug}"
    print(f"Scraping {county_name}: {url}")
    
    try:
        start_time = time.time()
        response = requests.get(url, headers=HEADERS, timeout=30)
        duration = time.time() - start_time
        
        if response.status_code != 200:
            print(f"Failed to fetch {county_name}: {response.status_code}")
            return None
            
        print(f"  Downloaded page in {duration:.2f}s. Parsing...")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for rows in the county list
        rows = soup.find_all('div', class_='div-table-row')
        
        best_url = None
        
        # Priority list for row names
        priorities = [
            "Assessor",
            "Property",
            "Tax",
            "GIS",
            "Mapping",
            "Auditor",
            "Treasurer",
            "Recorder"
        ]
        
        found_links = {}

        for row in rows:
            name_div = row.find('div', {'col-name': 'Name'})
            online_div = row.find('div', {'col-name': 'Online'})
            
            if name_div and online_div:
                name_text = name_div.get_text(strip=True)
                link = online_div.find('a')
                if link:
                    href = link.get('href')
                    if isinstance(href, list):
                        href = href[0]
                    if href and isinstance(href, str) and href.startswith('http'):
                        found_links[name_text] = href
        
        # Find the best match
        for priority in priorities:
            for name, href in found_links.items():
                if priority.lower() in name.lower():
                    return href
        
        # If no priority match, take the first one that isn't "Historic Aerials"
        for name, href in found_links.items():
            if "Historic Aerials" not in name:
                return href
                
        return None

    except Exception as e:
        print(f"Error scraping {county_name}: {e}")
        return None

def get_county_url(county_name):
    """
    Retrieves the county URL from cache or scrapes it if missing.
    """
    # Normalize county name (remove "County" suffix if present for matching)
    clean_name = county_name.replace(" County", "").strip()
    
    cache = load_cache()
    
    # Check cache (try exact, then clean)
    if county_name in cache:
        return cache[county_name]
    if clean_name in cache:
        return cache[clean_name]
        
    # Not in cache, need to scrape
    print(f"URL for {county_name} not in cache. Fetching...")
    
    # We need the slug. Do we have a slug cache? 
    # For simplicity, let's fetch all slugs if we don't have a mapping.
    # Or just try to guess the slug? Guessing is risky.
    # Let's fetch slugs.
    slugs = get_county_slugs()
    
    target_slug = slugs.get(clean_name)
    if not target_slug:
        # Try case insensitive
        for name, slug in slugs.items():
            if name.lower() == clean_name.lower():
                target_slug = slug
                break
    
    if target_slug:
        url = scrape_county_url(clean_name, target_slug)
        if url:
            cache[clean_name] = url
            save_cache(cache)
            return url
    
    return ""

def main():
    slugs = get_county_slugs()
    print(f"Found {len(slugs)} counties.")
    
    cache = load_cache()
    
    for name, slug in slugs.items():
        if name in cache:
            print(f"Skipping {name} (already cached)")
            continue
            
        url = scrape_county_url(name, slug)
        if url:
            print(f"  Found URL for {name}: {url}")
            cache[name] = url
            save_cache(cache) # Save incrementally
        else:
            print(f"  No URL found for {name}")
        
        time.sleep(random.uniform(1.0, 2.0))

if __name__ == "__main__":
    main()
