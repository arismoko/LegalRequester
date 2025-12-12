import cloudscraper
import json
from Counties.BaseScraper import CountyScraper
from Counties.models import ParcelInformation

class WashingtonCountyScraper(CountyScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://mn-washington.publicaccessnow.com"
        self.api_base = "/DesktopModules/QuickSearch/API"
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "ModuleId": "438",
            "TabId": "49",
            "X-Requested-With": "XMLHttpRequest"
        }

    def _search(self, query, page=1):
        controller = "Module"
        url = f"{self.base_url}{self.api_base}/{controller}/GetData"
        
        params = {
            "keywords": query,
            "page": page
        }
        
        try:
            response = self.scraper.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"Exception: {e}")
            return None

    def search_by_address(self, street_num, street_name):
        query = f"{street_num} {street_name}"
        data = self._search(query)
        
        results = []
        if data and 'items' in data:
            for item in data['items']:
                fields = item.get('fields', {})
                
                # Construct address from fields if Situs is empty, or just use Situs
                address = fields.get('Situs', '')
                if not address:
                    # Fallback to constructing it
                    parts = [
                        fields.get('Situsstreetnumber', ''),
                        fields.get('Situsstreetdirection', ''),
                        fields.get('Situsstreetname', ''),
                        fields.get('Situsstreettype', '')
                    ]
                    address = " ".join(p for p in parts if p).strip()

                result = ParcelInformation(
                    parcel_id=fields.get('ParcelID', ''),
                    owner=fields.get('Owner', ''),
                    address=address
                )
                results.append(result)
        
        return results

    def search_by_parcel(self, parcel_id):
        data = self._search(parcel_id)
        results = []
        if data and 'items' in data:
            for item in data['items']:
                fields = item.get('fields', {})
                result = ParcelInformation(
                    parcel_id=fields.get('ParcelID', ''),
                    owner=fields.get('Owner', ''),
                    address=fields.get('Situs', '')
                )
                results.append(result)
        return results

if __name__ == "__main__":
    scraper = WashingtonCountyScraper()
    # Example search
    results = scraper.search_by_address("1178", "Mckusick")
    for res in results:
        print(res.to_dict())

if __name__ == "__main__":
    def print_results(data, search_term):
        if not data:
            print(f"No results found for {search_term}")
        elif len(data) == 1:
            item = data[0]
            print(item.to_dict())
        else:
            print(f"Error: Multiple addresses found for {search_term}:")
            for item in data:
                print(item.to_dict())

    print("\n--- Washington County (Single) ---")
    washington_scraper = WashingtonCountyScraper()
    washington_data = washington_scraper.search_by_address("1178", "Mckusick")
    print_results(washington_data, "1178 Mckusick")
