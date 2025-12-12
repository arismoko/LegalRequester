import json
import os
from geopy.geocoders import Nominatim

def get_app_ids():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, 'appids.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_beacon_app_id(county, state, app_ids=None):
    if app_ids is None:
        app_ids = get_app_ids()
    
    if state not in app_ids:
        return None
    
    # Try exact match
    if county in app_ids[state]:
        return app_ids[state][county]
        
    # Try appending/removing " County"
    if "County" not in county:
        c_try = f"{county} County"
        if c_try in app_ids[state]:
            return app_ids[state][c_try]
    else:
        c_try = county.replace(" County", "")
        if c_try in app_ids[state]:
            return app_ids[state][c_try]
            
    return None

def find_beacon_app_id(address):
    """
    Finds the Beacon App ID for a given address string.
    
    Args:
        address (str): The full address string (e.g., "2346 Belmont, MN").
        
    Returns:
        str: The App ID, or None if not found.
    """
    geolocator = Nominatim(user_agent="LegalRequester_Project", timeout=10)
    
    try:
        location = geolocator.geocode(address, addressdetails=True)
        
        if not location:
            print(f"Address not found: {address}")
            return None
            
        address_details = location.raw.get('address', {})
        county = address_details.get('county')
        state = address_details.get('state')
        
        if not county or not state:
            print(f"Could not determine county or state for: {address}")
            return None
            
        # Load appids.json
        app_ids = get_app_ids()
            
        # Check if state exists
        if state not in app_ids:
            print(f"State '{state}' not found in appids.json")
            return None
            
        # Check if county exists
        app_id = get_beacon_app_id(county, state, app_ids)
        if app_id:
            return app_id
        
        print(f"County '{county}' not found in {state} list.")
        return None

    except Exception as e:
        print(f"Error finding App ID: {e}")
        return None
