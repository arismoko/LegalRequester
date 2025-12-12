import json
import os
from Counties.BeaconSchneiderCorp.utils import get_app_ids, get_beacon_app_id
from Counties.EagleWeb.scraper import EagleWebScraper

# List of all 87 Minnesota Counties
MN_COUNTIES = [
    "Aitkin", "Anoka", "Becker", "Beltrami", "Benton", "Big Stone", "Blue Earth", "Brown", 
    "Carlton", "Carver", "Cass", "Chippewa", "Chisago", "Clay", "Clearwater", "Cook", 
    "Cottonwood", "Crow Wing", "Dakota", "Dodge", "Douglas", "Faribault", "Fillmore", 
    "Freeborn", "Goodhue", "Grant", "Hennepin", "Houston", "Hubbard", "Isanti", "Itasca", 
    "Jackson", "Kanabec", "Kandiyohi", "Kittson", "Koochiching", "Lac qui Parle", "Lake", 
    "Lake of the Woods", "Le Sueur", "Lincoln", "Lyon", "McLeod", "Mahnomen", "Marshall", 
    "Martin", "Meeker", "Mille Lacs", "Morrison", "Mower", "Murray", "Nicollet", "Nobles", 
    "Norman", "Olmsted", "Otter Tail", "Pennington", "Pine", "Pipestone", "Polk", "Pope", 
    "Ramsey", "Red Lake", "Redwood", "Renville", "Rice", "Rock", "Roseau", "St. Louis", 
    "Scott", "Sherburne", "Sibley", "Stearns", "Steele", "Stevens", "Swift", "Todd", 
    "Traverse", "Wabasha", "Wadena", "Waseca", "Washington", "Watonwan", "Wilkin", 
    "Winona", "Wright", "Yellow Medicine"
]

def is_manually_supported(county_name):
    # Logic from search.py
    # Note: search.py checks "if 'Anoka' in county" where county usually includes " County"
    # Here we just have the name, so we check if the name matches the key keywords
    
    c = county_name
    if "Anoka" in c: return True
    if "Washington" in c: return True
    if "Crow Wing" in c: return True
    if "Hennepin" in c: return True
    if "Clearwater" in c: return True
    if "Aitkin" in c: return True
    return False

def find_unsupported_counties():
    print("Checking support for all Minnesota counties...")
    
    # Load Beacon Data
    beacon_app_ids = get_app_ids()
    
    unsupported = []
    supported_count = 0
    
    for county in MN_COUNTIES:
        county_full = f"{county} County"
        state = "Minnesota"
        
        is_supported = False
        support_source = []
        
        # 1. Check Beacon
        # get_beacon_app_id expects "CountyName County" usually, let's check how it handles it
        # It iterates through keys in app_ids['Minnesota'] and checks if key is in county_string
        if get_beacon_app_id(county_full, state, beacon_app_ids):
            is_supported = True
            support_source.append("Beacon")
            
        # 2. Check EagleWeb
        # EagleWebScraper.is_supported checks against counties.json
        if EagleWebScraper.is_supported(county_full):
            is_supported = True
            support_source.append("EagleWeb")
            
        # 3. Check Manual
        if is_manually_supported(county):
            is_supported = True
            support_source.append("Manual")
            
        if is_supported:
            supported_count += 1
            # print(f"[OK] {county}: {', '.join(support_source)}")
        else:
            print(f"[MISSING] {county}")
            unsupported.append(county)
            
    print(f"\nSummary:")
    print(f"Total Counties: {len(MN_COUNTIES)}")
    print(f"Supported: {supported_count}")
    print(f"Unsupported: {len(unsupported)}")
    
    output_file = "unsupported_mn_counties.json"
    with open(output_file, 'w') as f:
        json.dump(unsupported, f, indent=4)
        
    print(f"\nUnsupported list saved to {output_file}")

if __name__ == "__main__":
    find_unsupported_counties()
