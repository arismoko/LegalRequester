import json
import os
import time
from geopy.geocoders import Nominatim
from scourgify import normalize_address_record
from Counties.models import ParcelInformation
from Counties.BeaconSchneiderCorp.scraper import BeaconSchneiderCorpCountyScraper
from Counties.BeaconSchneiderCorp.utils import get_beacon_app_id, get_app_ids
from Counties.Anoka.scraper import AnokaCountyScraper
from Counties.Washington.scraper import WashingtonCountyScraper
from Counties.CrowWing.scraper import CrowWingCountyScraper
from Counties.Hennepin.scraper import HennepinCountyScraper
from Counties.Clearwater.scraper import ClearwaterCountyScraper
from Counties.EagleWeb.scraper import EagleWebScraper
from Counties.Aitkin.scraper import AitkinCountyScraper
from Counties.Becker.scraper import BeckerCountyScraper
from Counties.Beltrami.scraper import BeltramiCountyScraper
from Counties.Chisago.scraper import ChisagoCountyScraper
from Counties.Clay.scraper import ClayCountyScraper
from Counties.ActDataScout.scraper import ActDataScoutScraper
from scrape_county_urls import get_county_url

ALL_SCRAPERS = [
    BeaconSchneiderCorpCountyScraper,
    EagleWebScraper,
    ActDataScoutScraper,
    AnokaCountyScraper,
    WashingtonCountyScraper,
    CrowWingCountyScraper,
    HennepinCountyScraper,
    ClearwaterCountyScraper,
    AitkinCountyScraper,
    BeckerCountyScraper,
    BeltramiCountyScraper,
    ChisagoCountyScraper,
    ClayCountyScraper
]

def update_all_scraper_data():
    """
    Checks every scraper for a static update_data function and calls it.
    """
    print("Checking for scraper updates...")
    for scraper in ALL_SCRAPERS:
        if hasattr(scraper, 'update_data') and callable(scraper.update_data):
            print(f"Updating data for {scraper.__name__}...")
            try:
                scraper.update_data()
            except Exception as e:
                print(f"Error updating {scraper.__name__}: {e}")

STREET_SUFFIXES = {
    # Directions
    'n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw',
    'north', 'south', 'east', 'west', 
    'northeast', 'northwest', 'southeast', 'southwest',
    # Street Types
    'lane', 'ln', 'road', 'rd', 'street', 'st', 'avenue', 'ave', 
    'drive', 'dr', 'court', 'ct', 'circle', 'cir', 'boulevard', 'blvd', 
    'way', 'place', 'pl', 'terrace', 'ter', 'trail', 'trl', 
    'parkway', 'pkwy', 'highway', 'hwy', 'pike', 'pk', 'square', 'sq',
    'loop', 'lp', 'run', 'cove', 'cv', 'trace', 'trce', 'crossing', 'xing',
    'grove', 'grv', 'heights', 'hts', 'ridge', 'rdg', 'valley', 'vly',
    'alley', 'aly', 'path', 'walk', 'plaza', 'plz', 'point', 'pt',
    'bay', 'bend', 'view', 'vw'
}

def _clean_street_name(street):
    """
    Removes common suffixes (types and directions) from the end of the street name
    to improve search compatibility with county websites.
    """
    if not street:
        return street
        
    words = street.split()
    # Iterate backwards
    while words:
        last_word = words[-1].lower().replace('.', '')
        if last_word in STREET_SUFFIXES:
            words.pop()
        else:
            break
            
    return " ".join(words)

def _get_street_variants(street, house_num=None):
    """
    Generates a list of street name variants by using scourgify to normalize,
    and then progressively removing suffixes.
    Only returns UPPERCASE variants.
    Example: "7355 Keats Avenue North" -> ["KEATS AVE N", "KEATS AVE", "KEATS"]
    """
    if not street:
        return []
        
    variants = []

    # Helper to get scourgified street
    def get_scourgified_street(s, h_num):
        try:
            fake_num = h_num if h_num else "1"
            full_addr = f"{fake_num} {s}"
            normalized = normalize_address_record(full_addr)
            line1 = normalized.get('address_line_1', '')
            if line1.startswith(str(fake_num)):
                return line1[len(str(fake_num)):].strip()
            return line1
        except Exception:
            return s.upper()

    base_street = get_scourgified_street(street, house_num)
    if base_street:
        if base_street not in variants:
            variants.append(base_street)
    
    # Now strip suffixes from base_street
    words = base_street.split()
    while words:
        last_word = words[-1].lower().replace('.', '')
        if last_word in STREET_SUFFIXES:
            words.pop()
            if words:
                sub_street = " ".join(words)
                if sub_street not in variants:
                    variants.append(sub_street)
        else:
            break
            
    return variants


def _get_geocoded_locations(address_string):
    geolocator = Nominatim(user_agent="LegalRequester_Project", timeout=10)
    
    # Try with the requested limit first
    try:
        locations = geolocator.geocode(address_string, addressdetails=True, exactly_one=False, limit=50, country_codes='us')
        if locations:
            return _process_locations(locations, address_string)
    except Exception as e:
        if "503" in str(e):
            print("Warning: 503 Service Unavailable (Query likely too broad). Retrying with lower limit...")
            time.sleep(1) # Be polite to the server
            try:
                # Retry with a much smaller limit to reduce server load
                locations = geolocator.geocode(address_string, addressdetails=True, exactly_one=False, limit=1, country_codes='us')
                if locations:
                    return _process_locations(locations, address_string)
            except Exception as e2:
                if "503" in str(e2):
                     return None, ["Error: The address query is too broad for the geocoding service. Please add a City, State, or Zip Code."]
                return None, [f"Error geocoding address (Retry failed): {e2}"]
        else:
            return None, [f"Error geocoding address: {e}"]

    return None, ["Address not found."]

def _process_locations(locations, address_string):
    print(f"DEBUG: Found {len(locations)} locations for '{address_string}':")
    for i, loc in enumerate(locations):
        print(f"  {i+1}. [{loc.raw.get('class', 'unknown')}/{loc.raw.get('type', 'unknown')}] {loc.address}")

    # Filter out non-property results (boundaries, natural features)
    filtered_locations = []
    ignored_types = ['boundary', 'natural', 'waterway']
    for loc in locations:
        if loc.raw.get('class') not in ignored_types:
            filtered_locations.append(loc)
            
    if not filtered_locations:
        return None, ["No matching property addresses found (ignored administrative/natural locations)."]
        
    return filtered_locations, None

def FindPropertyDetails(address_string):
    """
    Finds property details for a given address string by identifying the county
    and using the appropriate scraper.
    
    Args:
        address_string (str): The full address string (e.g., "2346 Belmont, MN").
        
    Returns:
        list: A list of PropertyResult objects or error strings.
    """
    locations, errors = _get_geocoded_locations(address_string)
    if errors:
        return {"Error": errors}

    results = {}
    processed_searches = set()
    app_ids = get_app_ids()
    partial_matches = []

    # Group locations by county/state to aggregate searches
    grouped_locations = {}
    for loc in locations:
        addr = loc.raw.get('address', {})
        county = addr.get('county')
        state = addr.get('state')
        
        if not county or not state:
            continue

        house_num = addr.get('house_number')
        street = addr.get('road')
        
        if not house_num or not street:
             partial_matches.append(loc.address)
             continue
        
        key = (county, state)
        if key not in grouped_locations:
            grouped_locations[key] = []
        
        # Store the raw street name and the house number
        grouped_locations[key].append({'house_num': house_num, 'street': street, 'full_address': loc.address})

    for (county, state), loc_list in grouped_locations.items():
        print(f"Processing {county}, {state}...")
        county_key = f"{county}, {state}"
        if county_key not in results:
            results[county_key] = []
        
        # Build the list of search terms for this county
        # 1. All unique raw street names found in geocoding
        search_terms = []
        seen_terms = set()
        
        # We need to group by house number because we search by (house_num, street)
        # But wait, the scraper takes (house_num, street).
        # So we should iterate over the unique (house_num, street) pairs found.
        
        unique_locs = []
        seen_locs = set()
        
        for l in loc_list:
            k = (l['house_num'], l['street'])
            if k not in seen_locs:
                seen_locs.add(k)
                
                # Calculate display address
                display_address = l['full_address']
                try:
                    norm = normalize_address_record(l['full_address'])
                    parts = []
                    if norm.get('address_line_1'): parts.append(norm['address_line_1'])
                    if norm.get('address_line_2'): parts.append(norm['address_line_2'])
                    
                    city_val = norm.get('city', '')
                    if city_val and county:
                        c_upper = city_val.upper()
                        cnt_upper = county.upper()
                        if cnt_upper in c_upper:
                            city_val = c_upper.replace(cnt_upper, '').strip(', ')

                    city_state_parts = []
                    if city_val: city_state_parts.append(city_val)
                    if norm.get('state'): city_state_parts.append(norm['state'])
                    
                    suffix_str = ", ".join(city_state_parts)
                    
                    if norm.get('postal_code'):
                        suffix_str += " " + norm['postal_code']
                    
                    if suffix_str.strip():
                        parts.append(suffix_str.strip())
                    
                    if parts:
                        display_address = ", ".join(parts)
                except Exception:
                    pass
                
                l['display_address'] = display_address
                unique_locs.append(l)
        
        final_search_list = [] # List of (house_num, street_name, display_address) tuples
        added_search_keys = set()
        
        for l in unique_locs:
            display_address = l['display_address']

            # Only use variants generated by _get_street_variants (Scourgified + Pruned)
            variants = _get_street_variants(l['street'], l['house_num'])
            for v in variants:
                key = (l['house_num'], v)
                if key not in added_search_keys:
                    added_search_keys.add(key)
                    final_search_list.append((l['house_num'], v, display_address))
        
        print(f"DEBUG: Generated {len(final_search_list)} search variants for {county}, {state}.")
        any_scraper_ran = False

        # Helper to run search with variants and deduplicate
        def run_search_with_variants(scraper_instance):
            found_items = []
            seen_ids = set()
            
            print(f"DEBUG: Starting search loop for {len(final_search_list)} variants...")
            for i, (h_num, s_name, display_addr) in enumerate(final_search_list):
                print(f"  [{i+1}/{len(final_search_list)}] Searching for '{h_num} {s_name}'...") 
                data = scraper_instance.search_by_address(h_num, s_name)
                if data:
                    count_new = 0
                    for item in data:
                        # Override address with standardized display address
                        if isinstance(item, dict):
                            item['address'] = display_addr
                        elif hasattr(item, 'address'):
                            item.address = display_addr

                        # Try to identify unique items by parcel_id
                        pid = None
                        if isinstance(item, dict):
                            pid = item.get('parcel_id')
                        elif hasattr(item, 'parcel_id'):
                            pid = item.parcel_id
                        
                        if pid:
                            if pid not in seen_ids:
                                seen_ids.add(pid)
                                found_items.append(item)
                                count_new += 1
                        else:
                            # If no parcel_id, just add it (or check full equality?)
                            if item not in found_items:
                                found_items.append(item)
                                count_new += 1
                    print(f"    -> Found {len(data)} results ({count_new} new unique).")
                else:
                    print("    -> No results.")
            
            print(f"DEBUG: Total unique properties found: {len(found_items)}")
            return found_items

        # 1. Check Beacon
        app_id = get_beacon_app_id(county, state, app_ids)
        if app_id:
            any_scraper_ran = True
            print(f"Found Beacon App ID {app_id} for {county}, {state}")
            try:
                scraper = BeaconSchneiderCorpCountyScraper(app_id)
                results[county_key].extend(run_search_with_variants(scraper))
            except Exception as e:
                results[county_key].append(f"Error scraping Beacon for {county}: {e}")

        # 2. Check EagleWeb
        if EagleWebScraper.is_supported(county):
            any_scraper_ran = True
            print(f"Found EagleWeb support for {county}, {state}")
            try:
                scraper = EagleWebScraper(county)
                results[county_key].extend(run_search_with_variants(scraper))
            except Exception as e:
                results[county_key].append(f"Error scraping EagleWeb for {county}: {e}")
            
        # 3. Check ActDataScout
        if ActDataScoutScraper.is_supported(county, state):
            any_scraper_ran = True
            print(f"Found ActDataScout support for {county}, {state}")
            try:
                scraper = ActDataScoutScraper(county, state)
                results[county_key].extend(run_search_with_variants(scraper))
            except Exception as e:
                results[county_key].append(f"Error scraping ActDataScout for {county}: {e}")

        # 4. Check Manual Scrapers
        scraper_cls = None
        
        if state == "Minnesota":
            if "Anoka" in county: scraper_cls = AnokaCountyScraper
            elif "Washington" in county: scraper_cls = WashingtonCountyScraper
            elif "Crow Wing" in county: scraper_cls = CrowWingCountyScraper
            elif "Hennepin" in county: scraper_cls = HennepinCountyScraper
            elif "Clearwater" in county: scraper_cls = ClearwaterCountyScraper
            elif "Aitkin" in county: scraper_cls = AitkinCountyScraper
            elif "Becker" in county: scraper_cls = BeckerCountyScraper
            elif "Beltrami" in county: scraper_cls = BeltramiCountyScraper
            elif "Chisago" in county: scraper_cls = ChisagoCountyScraper
            elif "Clay" in county: scraper_cls = ClayCountyScraper
            
        if scraper_cls:
            any_scraper_ran = True
            print(f"Using manual scraper {scraper_cls.__name__} for {county}, {state}")
            try:
                scraper = scraper_cls()
                results[county_key].extend(run_search_with_variants(scraper))
            except Exception as e:
                results[county_key].append(f"Error scraping {county}: {e}")
        
        # Populate county URL for found results
        if county_key in results and results[county_key]:
             # Only fetch if we have actual results (ParcelInformation objects)
             has_objects = any(hasattr(item, 'county_url') for item in results[county_key])
             if has_objects:
                 try:
                     c_url = get_county_url(county)
                     for item in results[county_key]:
                         if hasattr(item, 'county_url') and not item.county_url:
                             item.county_url = c_url
                 except Exception as e:
                     print(f"Error fetching county URL: {e}")

        # If we have no results yet (either no scraper ran, or they all returned nothing)
        if county_key not in results or not results[county_key]:
            reason = "No scraper found" if not any_scraper_ran else "Scrapers returned no results"
            print(f"{reason} for {county}, {state}. Creating stub results.")
            
            c_url = ""
            try:
                c_url = get_county_url(county)
            except Exception as e:
                print(f"Error fetching county URL: {e}")

            stubs = []
            for l in unique_locs:
                stubs.append(ParcelInformation(
                    parcel_id=None,
                    owner=None,
                    address=l['display_address'],
                    county_url=c_url
                ))
            
            if "Error" not in results:
                results["Error"] = []
            results["Error"].extend(stubs)
            
            if county_key in results and not results[county_key]:
                del results[county_key]

    if not results and partial_matches:
        return {"Partial Matches": ["Found the following locations, but could not determine house number. Please provide a complete address:"] + [f"- {m}" for m in partial_matches]}

    return results

