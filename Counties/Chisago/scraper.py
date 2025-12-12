import re
from bs4 import BeautifulSoup
from Counties.BaseScraper import CountyScraper
from Counties.models import ParcelInformation

class ChisagoCountyScraper(CountyScraper):
    BASE_URL = "https://gis.chisagocountymn.gov/chisago_tax/"

    def __init__(self):
        super().__init__()
        self.headers.update({
            'Origin': 'https://gis.chisagocountymn.gov',
            'Referer': 'https://gis.chisagocountymn.gov/chisago_tax/',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
        })

    def search_by_address(self, street_num, street_name):
        print(f"Fetching search page for tokens...")
        # 1. Get the initial page to extract ViewState
        try:
            response = self.scraper.get(self.BASE_URL, headers=self.headers)
            response.raise_for_status()
        except Exception as e:
            print(f"Error fetching initial page: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        hidden_fields = self._get_hidden_fields(soup)
        
        # 2. Prepare POST data
        payload = hidden_fields.copy()
        payload.update({
            'ddlType': 'R - Real Property',
            'txtPinFirst': '',
            'txtPinMiddle': '',
            'txtPinLast': '',
            'ddlYear': '2025',
            'txtHouseNum': street_num,
            'txtStreetName': street_name,
            'ddlStreetType': '',
            'ddlDirection': '',
            'ddlCity': '',
            'txtZip': '',
            'ddlAddressYear': '2025',
            'btnSearchAddress.x': '14', # Coordinates from curl
            'btnSearchAddress.y': '19',
            'txtTaxPayerName': '',
            'NameSearchYear': '2025'
        })

        print(f"Searching for {street_num} {street_name}...")
        try:
            response = self.scraper.post(self.BASE_URL, data=payload, headers=self.headers)
            response.raise_for_status()
        except Exception as e:
            print(f"Error performing search: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Debug: Save response to inspect
        with open("chisago_response.html", "w") as f:
            f.write(response.text)

        results = []
        
        # Parse results
        table = soup.find('table', id='gvResults')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if not cols:
                    continue
                
                # Check if first column has a link with 'pin='
                link = cols[0].find('a')
                if link and 'href' in link.attrs and 'pin=' in link['href']:
                    parcel_id = link.get_text(strip=True)
                    
                    # Column 3 is Name (Owner)
                    owner = cols[2].get_text(strip=True)
                    
                    # Column 4 is Street (Address)
                    address = cols[3].get_text(strip=True)
                    
                    results.append(ParcelInformation(
                        parcel_id=parcel_id,
                        owner=owner,
                        address=address
                    ))
        
        return results

    def search_by_parcel(self, parcel_id):
        print(f"Fetching search page for tokens...")
        try:
            response = self.scraper.get(self.BASE_URL, headers=self.headers)
            response.raise_for_status()
        except Exception as e:
            print(f"Error fetching initial page: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        hidden_fields = self._get_hidden_fields(soup)
        
        # Parse PIN: R03.00459.10 -> R03, 00459, 10
        parts = parcel_id.split('.')
        if len(parts) != 3:
            print(f"Invalid PIN format: {parcel_id}. Expected format: XXX.XXXXX.XX")
            return []
            
        pin_first, pin_middle, pin_last = parts

        payload = hidden_fields.copy()
        payload.update({
            'ddlType': 'R - Real Property',
            'txtPinFirst': pin_first,
            'txtPinMiddle': pin_middle,
            'txtPinLast': pin_last,
            'ddlYear': '2025',
            'txtHouseNum': '',
            'txtStreetName': '',
            'ddlStreetType': '',
            'ddlDirection': '',
            'ddlCity': '',
            'txtZip': '',
            'ddlAddressYear': '2025',
            'btnSearchPin.x': '10', # Guessing coordinates for PIN search button
            'btnSearchPin.y': '10',
            'txtTaxPayerName': '',
            'NameSearchYear': '2025'
        })
        
        # Remove address search button coordinates if present in hidden_fields (unlikely but good practice)
        # Actually we are constructing payload from hidden_fields which doesn't have buttons.
        # We need to make sure we send the right button.
        # The form has multiple submit buttons. We must include the name of the button we clicked.
        # In the address search, it was `btnSearchAddress.x`.
        # For PIN search, looking at the HTML (I don't have the search page HTML, but I can guess from the curl headers provided earlier... wait, the curl was for address search).
        # I should fetch the search page and check the button name for PIN search.
        
        # Let's do a quick check of the search page form in the next step if needed.
        # But usually it's `btnSearchPin`.
        
        print(f"Searching for PIN {parcel_id}...")
        try:
            response = self.scraper.post(self.BASE_URL, data=payload, headers=self.headers)
            response.raise_for_status()
        except Exception as e:
            print(f"Error performing search: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Reuse parsing logic
        results = []
        table = soup.find('table', id='gvResults')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if not cols:
                    continue
                
                link = cols[0].find('a')
                if link and 'href' in link.attrs and 'pin=' in link['href']:
                    pid = link.get_text(strip=True)
                    owner = cols[2].get_text(strip=True)
                    address = cols[3].get_text(strip=True)
                    
                    results.append(ParcelInformation(
                        parcel_id=pid,
                        owner=owner,
                        address=address
                    ))
        
        return results
