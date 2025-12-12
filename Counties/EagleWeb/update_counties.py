import json
import os
import re
import cloudscraper
from bs4 import BeautifulSoup

def update_counties(output_file=None):
    if output_file is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(base_dir, 'counties.json')

    print("Fetching data from EagleWeb (CPTMN)...")
    scraper = cloudscraper.create_scraper()
    
    try:
        # The site is an Angular SPA, so we hit the API directly.
        api_url = "https://tax.cptmn.us/PTaxPortal/servlet/ControllerTaxWeb?message=getCounties"
        response = scraper.post(api_url)
        
        if response.status_code != 200:
            print(f"Failed to fetch API. Status code: {response.status_code}")
            return

        try:
            data = response.json()
        except json.JSONDecodeError:
            print("Failed to decode JSON response.")
            return

        counties = {}
        for item in data:
            name = item.get('desc')
            cid = item.get('id')
            # Filter out test/invalid entries if necessary (e.g. "CPTTEST")
            if name and cid and name != "CPTTEST":
                # Clean name if needed, but usually 'desc' is clean enough
                counties[name] = cid
        
        if not counties:
            print("Warning: No counties found in the API response.")
            return

        # Sort by name
        sorted_counties = dict(sorted(counties.items()))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_counties, f, indent=4)
        
        print(f"Successfully updated {output_file} with {len(counties)} counties.")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    update_counties()
