import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urlparse, parse_qs

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'DNT': '1',
    'Sec-GPC': '1',
    'Priority': 'u=0, i'
}

CACHE_FILE = os.path.join(os.path.dirname(__file__), 'counties.json')

def update_counties():
    print("Fetching ActDataScout homepage...")
    try:
        response = requests.get("https://www.actdatascout.com/", headers=HEADERS)
        if response.status_code != 200:
            print(f"Failed to fetch homepage: {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a')
        
        county_links = []
        for link in links:
            href = link.get('href')
            if isinstance(href, list):
                href = href[0]
            
            text = link.get_text(strip=True)
            if href and isinstance(href, str) and '/RealProperty/' in href:
                # Format: /RealProperty/{State}/{County}
                if href.startswith('http'):
                    full_url = href
                else:
                    full_url = f"https://www.actdatascout.com{href}"
                
                parts = href.split('/')
                # Handle cases where href might be absolute or relative for splitting
                # If absolute, parts will have http, empty, domain, RealProperty, State, County
                # If relative, parts will have empty, RealProperty, State, County
                
                try:
                    if 'RealProperty' in parts:
                        idx = parts.index('RealProperty')
                        if len(parts) > idx + 2:
                            state = parts[idx+1]
                            county = parts[idx+2]
                            county_links.append({
                                'state': state,
                                'county': county,
                                'url': full_url
                            })
                except:
                    pass

        print(f"Found {len(county_links)} potential counties.")
        
        counties_data = {}
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    counties_data = json.load(f)
            except:
                pass

        for item in county_links:
            state = item['state']
            county = item['county']
            
            # Skip if we already have the ID
            if state in counties_data and county in counties_data[state]:
                continue
                
            print(f"Resolving ID for {county}, {state}...")
            try:
                # Follow redirect to get ID
                resp = requests.get(item['url'], headers=HEADERS, allow_redirects=False, timeout=10)
                if resp.status_code in [301, 302]:
                    location = resp.headers.get('Location')
                    if location and 'countyId=' in location:
                        parsed = urlparse(location)
                        qs = parse_qs(parsed.query)
                        county_id = qs.get('countyId', [None])[0]
                        
                        if county_id:
                            if state not in counties_data:
                                counties_data[state] = {}
                            counties_data[state][county] = county_id
                            print(f"  -> ID: {county_id}")
                            
                            # Save incrementally
                            with open(CACHE_FILE, 'w') as f:
                                json.dump(counties_data, f, indent=4)
                else:
                    print(f"  -> No redirect (Status: {resp.status_code})")
            except Exception as e:
                print(f"  -> Error: {e}")
            
            time.sleep(0.5) # Be polite

    except Exception as e:
        print(f"Error updating counties: {e}")

if __name__ == "__main__":
    update_counties()
