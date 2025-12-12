from Counties.BaseScraper import CountyScraper
from Counties.EagleWeb.update_counties import update_counties
from Counties.models import ParcelInformation
import json
import os
import urllib.parse

class EagleWebScraper(CountyScraper):
    @staticmethod
    def update_data():
        update_counties()

    @staticmethod
    def _get_county_id(county):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, 'counties.json')
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle both list (legacy) and dict formats for backward compatibility during transition
                if isinstance(data, list):
                    return None
                
                # Try exact match
                if county in data: return data[county]
                
                # Try removing " County"
                clean_name = county.replace(" County", "")
                if clean_name in data: return data[clean_name]
                
                return None
        except FileNotFoundError:
            return None

    @staticmethod
    def is_supported(county):
        return EagleWebScraper._get_county_id(county) is not None

    def __init__(self, county):
        super().__init__()
        self.county = county
        self.county_id = self._get_county_id(county)
        self.base_url = "https://tax.cptmn.us/PTaxPortal/"
        
        if not self.county_id:
            print(f"Warning: {self.county} ID not found. EagleWeb search will fail.")

    def search_by_address(self, house_num, street_name):
        if not self.county_id:
            print("Error: No County ID available.")
            return []

        address_query = f"{house_num} {street_name}"
        print(f"Searching EagleWeb ({self.county}, ID: {self.county_id}) for '{address_query}'...")
        
        # Construct API URL
        # https://tax.cptmn.us/PTaxPortal/servlet/ControllerTaxWeb?message=getAllParcels&address=900%203rd&cntyId=17
        encoded_address = urllib.parse.quote(address_query)
        api_url = f"https://tax.cptmn.us/PTaxPortal/servlet/ControllerTaxWeb?message=getAllParcels&address={encoded_address}&cntyId={self.county_id}"
        
        try:
            # The user provided headers, but cloudscraper usually handles most.
            # We'll add specific ones if needed.
            headers = {
                'Origin': 'https://tax.cptmn.us',
                'Referer': 'https://tax.cptmn.us/PTaxPortal/',
                'Content-Type': 'application/json'
            }
            
            # The user used --data-raw '{}', so we send an empty JSON object
            response = self.scraper.post(api_url, headers=headers, json={})
            
            if response.status_code != 200:
                print(f"Error: API returned status {response.status_code}")
                return []
                
            data = response.json()
            
            results = []
            for item in data:
                # Parse the item into ParcelInformation
                # Example item:
                # {"parcelNum":"25-820-0970", "taxpayer":{"name":"COUNTY OF COTTONWOOD","address1":"900 3RD AVE"}, ...}
                
                parcel_id = item.get('parcelNum')
                
                taxpayer = item.get('taxpayer', {})
                owner = taxpayer.get('name', '')
                
                # Construct address from parts
                addr_parts = [
                    taxpayer.get('address1'),
                    taxpayer.get('address2'),
                    taxpayer.get('address3'),
                    taxpayer.get('address4')
                ]
                address = ", ".join([p for p in addr_parts if p])
                
                if parcel_id:
                    result = ParcelInformation(
                        parcel_id=parcel_id,
                        owner=owner,
                        address=address
                    )
                    results.append(result)
            
            return results

        except Exception as e:
            print(f"Error searching EagleWeb: {e}")
            return []

    def search_by_parcel(self, parcel_id):
        # Placeholder for search logic
        print(f"Searching EagleWeb ({self.county}) for parcel {parcel_id}...")
        return []
