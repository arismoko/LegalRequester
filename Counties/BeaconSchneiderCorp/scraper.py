import re
from bs4 import BeautifulSoup
from Counties.BaseScraper import CountyScraper
from Counties.models import ParcelInformation
from Counties.BeaconSchneiderCorp.update_appids import update_appids

class BeaconSchneiderCorpCountyScraper(CountyScraper):
    @staticmethod
    def update_data():
        update_appids()

    def __init__(self, app_id):
        super().__init__()
        self.app_id = app_id
        self.base_url = f"https://beacon.schneidercorp.com/Application.aspx?AppID={app_id}&PageType=Search"
        self.headers['Origin'] = 'https://beacon.schneidercorp.com'
        self.headers['Alt-Used'] = 'beacon.schneidercorp.com'
        self.headers['Referer'] = self.base_url

    def search_by_address(self, street_num, street_name):
        print(f"Step 1: Fetching the search page to get tokens (AppID: {self.app_id})...")
        response = self.scraper.get(self.base_url, headers=self.headers)
        
        # Update base_url if redirected (e.g. to include PageID)
        if response.url != self.base_url:
            self.base_url = response.url
            self.headers['Referer'] = self.base_url
            
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
        post_response = self.scraper.post(self.base_url, data=payload, headers=self.headers)
        result_soup = BeautifulSoup(post_response.text, 'html.parser')
        
        results = []
        for row in result_soup.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 4:
                for br in cells[2].find_all("br"):
                    br.replace_with(" & ")

                parcel_id = cells[1].text.strip()
                
                raw_owner = cells[2].get_text()
                clean_owner = raw_owner.replace("(OWNER)", "")

                owner_with_amp = re.sub(r'\s{3,}', ' & ', clean_owner)
                

                owner = " ".join(owner_with_amp.split()).strip(" &")
                
                address = cells[3].text.strip()
                
                if parcel_id == "Parcel ID":
                    continue
                    
                results.append(ParcelInformation(
                    parcel_id=parcel_id,
                    owner=owner,
                    address=address
                ))

        return results

    def search_by_parcel(self, parcel_id):
        # Filler code for now
        print(f"Searching for parcel ID: {parcel_id} (Not implemented yet)")
        return []
