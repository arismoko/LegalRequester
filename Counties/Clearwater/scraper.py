import re
from bs4 import BeautifulSoup
from Counties.BaseScraper import CountyScraper
from Counties.models import ParcelInformation

class ClearwaterCountyScraper(CountyScraper):
    BASE_URL = "https://mn-clearwater.manatron.com/Tabs/TaxSearch.aspx"

    def __init__(self):
        super().__init__()
        self.headers.update({
            'Origin': 'https://mn-clearwater.manatron.com',
            'Referer': 'https://mn-clearwater.manatron.com/Tabs/TaxSearch.aspx',
        })

    def search_by_address(self, street_num, street_name):
        # 1. Get the initial page to get ViewState
        print("Fetching initial page...")
        response = self.scraper.get(self.BASE_URL, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        hidden_fields = self._get_hidden_fields(soup)
        
        # 2. Prepare the search payload
        search_term = f"{street_num} {street_name}".strip()
        
        payload = hidden_fields.copy()
        payload.update({
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            'dnn$dnnSEARCH$txtSearch': '',
            'selSearchBy': 'Column4*',  # Address
            'fldInput': search_term,
            'btnsearch': 'search',
            'selSortBy': 'Column2',
            'ScrollTop': '',
            '__dnnVariable': ''
        })

        print(f"Searching for {search_term}...")
        response = self.scraper.post(self.BASE_URL, data=payload, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        
        # 3. Parse results
        # Look for the results table with id="grm-search"
        table = soup.find('table', id='grm-search')
        if not table:
            return []

        for row in table.find_all('tr'):
            # Skip header row (th)
            if row.find('th'):
                continue
            
            # Extract columns
            # c2: Owner Name
            # c4: Property Address
            # c5: Parcel Number
            
            owner_cell = row.find('td', class_='c2')
            address_cell = row.find('td', class_='c4')
            parcel_cell = row.find('td', class_='c5')
            
            if parcel_cell:
                parcel_id = parcel_cell.get_text(strip=True)
                owner = owner_cell.get_text(strip=True) if owner_cell else ""
                address = address_cell.get_text(strip=True) if address_cell else ""
                
                results.append(ParcelInformation(
                    parcel_id=parcel_id,
                    owner=owner,
                    address=address
                ))

        return results

    def search_by_parcel(self, parcel_id):
        pass

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

    print("\n--- Clearwater County (Single) ---")
    clearwater_scraper = ClearwaterCountyScraper()
    clearwater_data = clearwater_scraper.search_by_address("213", "Main")
    print_results(clearwater_data, "213 Main")

    print("\n--- Clearwater County (Multiple) ---")
    clearwater_data = clearwater_scraper.search_by_address("", "Main")
    print_results(clearwater_data, "Main")
