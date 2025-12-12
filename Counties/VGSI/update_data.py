import json
import os
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def update_data(output_file=None):
    if output_file is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(base_dir, 'data.json')

    print("Fetching data from VGSI...")
    scraper = cloudscraper.create_scraper()
    
    base_url = "https://www.vgsi.com/taxpayer-info/"
    try:
        response = scraper.get(base_url)
        if response.status_code != 200:
            print(f"Failed to fetch base URL. Status code: {response.status_code}")
            return
    except Exception as e:
        print(f"Error fetching base URL: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    
    state_links = {}
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'online-database' in href:
            state_name = a.text.strip()
            if state_name:
                state_links[state_name] = href

    print(f"Found {len(state_links)} states.")

    all_data = {}

    for state, link in state_links.items():
        print(f"Fetching {state}...")
        try:
            resp = scraper.get(link)
            if resp.status_code != 200:
                print(f"Failed to fetch {state}. Status code: {resp.status_code}")
                continue
            
            state_soup = BeautifulSoup(resp.content, 'html.parser')
            counties = {}
            
            # Find links to gis.vgsi.com or hosting.vgsi.com
            for a in state_soup.find_all('a', href=True):
                href = a['href']
                text = a.text.strip()
                if ('gis.vgsi.com' in href or 'hosting.vgsi.com' in href) and text:
                    # Clean up text (remove state abbreviation if present, e.g. "Bloomington, MN" -> "Bloomington")
                    if ',' in text:
                        name = text.split(',')[0].strip()
                    else:
                        name = text
                    
                    counties[name] = href
            
            if counties:
                all_data[state] = dict(sorted(counties.items()))
                print(f"  Found {len(counties)} municipalities in {state}.")
            else:
                print(f"  No municipalities found in {state}.")

        except Exception as e:
            print(f"Error fetching {state}: {e}")

    if not all_data:
        print("No data found.")
        return

    # Sort by state name
    sorted_data = dict(sorted(all_data.items()))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_data, f, indent=4)
    
    print(f"Successfully updated {output_file}.")

if __name__ == "__main__":
    update_data()
