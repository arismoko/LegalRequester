import json
import re
import os
import cloudscraper

def update_appids(output_file=None):
    if output_file is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(base_dir, 'appids.json')

    print("Fetching data from Beacon...")
    scraper = cloudscraper.create_scraper()
    
    try:
        # Fetch the main page first to get cookies/tokens
        scraper.get("https://beacon.schneidercorp.com/")
        
        # Fetch the API endpoint
        api_url = "https://beacon.schneidercorp.com/api/globalsearch/framework"
        response = scraper.get(api_url)
        
        if response.status_code != 200:
            print(f"Failed to fetch API. Status code: {response.status_code}")
            return

        data = response.json()
        
        result = {}
        
        for state_entry in data.get('States', []):
            state_name = state_entry.get('Name')
            if not state_name:
                continue
                
            if state_name not in result:
                result[state_name] = {}
                
            for app in state_entry.get('Apps', []):
                app_id = str(app.get('ID'))
                display_name = app.get('DisplayName')
                
                if app_id and display_name:
                    # Clean the name
                    # Remove state abbreviation/name
                    # Pattern: comma, optional whitespace, 2 uppercase letters or "Iowa", word boundary
                    clean_name = re.sub(r',\s*([A-Z]{2}|Iowa)\b', '', display_name)
                    # Clean up extra whitespace
                    clean_name = re.sub(r'\s+', ' ', clean_name).strip()
                    
                    result[state_name][clean_name] = app_id
                    
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4)
        
        print(f"Successfully updated {output_file}")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    update_appids()
