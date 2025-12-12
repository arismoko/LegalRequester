from Counties.BaseScraper import CountyScraper
import urllib.parse

class AitkinCountyScraper(CountyScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://gisweb.co.aitkin.mn.us/arcgis/rest/services/ParcelSearch/MapServer/0/query"

    def search_by_address(self, street_num, street_name):
        # Construct the address string to search for
        # The API uses UPPER(Physical_Address) LIKE '%ADDRESS%'
        # We'll combine street_num and street_name
        address_query = f"{street_num} {street_name}".strip().upper()
        
        params = {
            'f': 'json',
            'where': f"UPPER(Physical_Address) LIKE '%{address_query}%'",
            'returnGeometry': 'false',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': '*',
            'outSR': '102100'
        }
        
        # Use requests to get the data
        # self.scraper is a cloudscraper instance, which is compatible with requests
        try:
            response = self.scraper.get(self.base_url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if 'features' in data:
                for feature in data['features']:
                    attrs = feature.get('attributes', {})
                    
                    # Map fields
                    parcel_id = attrs.get('PRINT_KEY')
                    owner = attrs.get('OWNNAME')
                    
                    # Construct full address from components if possible, or use Physical_Address
                    address = attrs.get('Physical_Address')
                    city = attrs.get('Physical_City')
                    zip_code = attrs.get('Physical_Zip')
                    
                    full_address = address
                    if city:
                        full_address += f", {city}"
                    if zip_code:
                        full_address += f" {zip_code}"
                        
                    results.append({
                        'parcel_id': parcel_id,
                        'owner': owner,
                        'address': full_address
                    })
            
            return results
            
        except Exception as e:
            print(f"Error searching Aitkin County: {e}")
            return []

    def search_by_parcel(self, parcel_id):
        # Implement if needed, similar to search_by_address but with PRINT_KEY
        pass
