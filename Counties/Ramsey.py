import re
from bs4 import BeautifulSoup
from .BaseScraper import CountyScraper
from .models import PropertyResult

class RamseyCountyScraper(CountyScraper):
    BASE_URL = "https://beacon.schneidercorp.com/Application.aspx?App=RamseyCountyMN&PageType=Search"

    def __init__(self):
        super().__init__()
        self.headers['Origin'] = 'https://beacon.schneidercorp.com'
        self.headers['Alt-Used'] = 'beacon.schneidercorp.com'
        self.headers['Referer'] = self.BASE_URL

    def search_by_address(self, street_num, street_name):
        print("Step 1: Fetching the search page to get tokens...")
        response = self.scraper.get(self.BASE_URL, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        hidden_fields = self._get_hidden_fields(soup)
        if not hidden_fields['__VIEWSTATE']:
            print("Error: Failed to retrieve search page tokens.")
            return []

        payload = {
            '__EVENTTARGET': 'ctlBodyPane$ctl01$ctl01$btnSplitAddresssSearch',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': hidden_fields['__VIEWSTATE'],
            '__VIEWSTATEGENERATOR': hidden_fields['__VIEWSTATEGENERATOR'],
            '__EVENTVALIDATION': hidden_fields['__EVENTVALIDATION'],
            'ctlBodyPane$ctl01$ctl01$txtStreetNumber': street_num,
            'ctlBodyPane$ctl01$ctl01$txtStreetName': street_name,
            'ctlBodyPane$ctl01$ctl01$txtAddress': '',
            'ctlBodyPane$ctl01$ctl01$txtAddressExact': '',
            'ctlBodyPane$ctl01$ctl01$txtUnitNumber': '',
            'ctlBodyPane$ctl02$ctl01$txtParcelID': '',
            'ctlBodyPane$ctl03$ctl01$hfPlatSelection': '[]',
            'ctlBodyPane$ctl03$ctl01$txtPlatName': '',
            'ctlBodyPane$ctl03$ctl01$hfBlockSelection': '[]',
            'ctlBodyPane$ctl03$ctl01$txtBlockName': '',
            'ctlBodyPane$ctl03$ctl01$hfLotSelection': '[]',
            'ctlBodyPane$ctl03$ctl01$txtBlockName': '',
            'ctlBodyPane$ctl03$ctl01$txtLotName': ''
        }

        print(f"Step 2: Searching for {street_num} {street_name}...")
        post_response = self.scraper.post(self.BASE_URL, data=payload, headers=self.headers)
        result_soup = BeautifulSoup(post_response.text, 'html.parser')
        
        results = []
        for row in result_soup.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 4:
                # 0: Checkbox/Empty
                # 1: Parcel ID
                # 2: Owner
                # 3: Address
                
                # Replace <br> tags with " & " to separate multiple owners
                for br in cells[2].find_all("br"):
                    br.replace_with(" & ")

                parcel_id = cells[1].text.strip()
                
                # Extract text and remove (OWNER)
                raw_owner = cells[2].get_text()
                clean_owner = raw_owner.replace("(OWNER)", "")
                
                # Replace 3 or more whitespace characters with " & "
                # This handles cases where names are separated by multiple spaces instead of <br>
                owner_with_amp = re.sub(r'\s{3,}', ' & ', clean_owner)
                
                # Final cleanup of extra spaces
                # Remove leading/trailing " & " if they were introduced by spaces at the start/end
                owner = " ".join(owner_with_amp.split()).strip(" &")
                
                address = cells[3].text.strip()
                
                # Filter out header rows if they get caught (usually they have th, but just in case)
                if parcel_id == "Parcel ID":
                    continue
                    
                results.append(PropertyResult(
                    parcel_id=parcel_id,
                    owner=owner,
                    address=address
                ))

        return results

    def search_by_parcel(self, parcel_id):
        # Filler code for now
        print(f"Searching for parcel ID: {parcel_id} (Not implemented yet)")
        return []
