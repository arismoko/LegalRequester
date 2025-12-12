import re
from bs4 import BeautifulSoup
from Counties.BaseScraper import CountyScraper
from Counties.models import ParcelInformation

class HennepinCountyScraper(CountyScraper):
    BASE_URL = "https://www16.co.hennepin.mn.us/pins/addrresult.jsp"

    def __init__(self):
        super().__init__()
        self.headers['Origin'] = 'https://www16.co.hennepin.mn.us'
        self.headers['Referer'] = 'https://www16.co.hennepin.mn.us/pins/?articleId=by_address'

    def search_by_address(self, street_num, street_name):
        payload = {
            'house': street_num,
            'street': street_name,
            'condo': '',
            'ps': '20'
        }

        print(f"Searching for {street_num} {street_name}...")
        response = self.scraper.post(self.BASE_URL, data=payload, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        
        # 1. Extract PID
        parcel_id = ""
        # Try to find it in links first as it's reliable there
        for link in soup.find_all('a'):
            href = link.get('href')
            if isinstance(href, str) and "pid=" in href:
                match = re.search(r'pid=(\d+)', href)
                if match:
                    parcel_id = match.group(1)
                    break
        
        # 2. Extract Owner
        owner = ""
        owner_tag = soup.find(string=lambda text: text is not None and "Owner name:" in text)
        if owner_tag:
            parent = owner_tag.parent
            if parent:
                next_div = parent.find_next_sibling('div')
                if next_div:
                    owner = next_div.get_text(strip=True)

        # 3. Extract Address
        address = ""
        # Look for "Address:" label
        addr_label = soup.find(string=lambda text: text is not None and "Address:" in text)
        if addr_label:
             parent = addr_label.parent
             if parent:
                 next_div = parent.find_next_sibling('div')
                 if next_div:
                     address = " ".join(next_div.get_text(strip=True).split())
        
        if parcel_id:
            results.append(ParcelInformation(
                parcel_id=parcel_id,
                owner=owner,
                address=address
            ))
            return results
            
        # Handle multiple results (Not implemented yet)
        # The server seems to error out on broad searches or returns a different format.
        # Without a working example of multiple results, we return empty list.
        
        return results

    def search_by_parcel(self, parcel_id):
        print(f"Searching for parcel ID: {parcel_id} (Not implemented yet)")
        return []

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

    print("\n--- Hennepin County (Single) ---")
    hennepin_scraper = HennepinCountyScraper()
    hennepin_data = hennepin_scraper.search_by_address("1024", "xene")
    print_results(hennepin_data, "1024 xene")

    print("\n--- Hennepin County (Multiple) ---")
    hennepin_scraper = HennepinCountyScraper()
    hennepin_data = hennepin_scraper.search_by_address("", "xene")
    print_results(hennepin_data, "xene")
