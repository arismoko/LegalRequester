from bs4 import BeautifulSoup
from Counties.BaseScraper import CountyScraper
from Counties.models import ParcelInformation

class CrowWingCountyScraper(CountyScraper):
    BASE_URL = "https://propertyinformation.crowwing.gov/search/CommonSearch.aspx?mode=REALPROP"

    def __init__(self):
        super().__init__()
        self.headers['Origin'] = 'https://propertyinformation.crowwing.gov'
        self.headers['Referer'] = self.BASE_URL
        self.headers['Cookie'] = 'DISCLAIMER=1'

    def search_by_address(self, street_num, street_name):
        print("Step 1: Fetching the search page to get tokens...")
        response = self.scraper.get(self.BASE_URL, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        hidden_fields = self._get_hidden_fields(soup)
        if not hidden_fields['__VIEWSTATE']:
            print("Error: Failed to retrieve search page tokens.")
            return []

        # TSM value from the curl command
        tsm_value = ';;AjaxControlToolkit, Version=4.1.50731.0, Culture=neutral, PublicKeyToken=28f01b0e84b6d53e:en-US:f8fb2a65-e23a-483b-b20e-6db6ef539a22:ea597d4b:b25378d2;Telerik.Web.UI, Version=2020.2.512.45, Culture=neutral, PublicKeyToken=121fae78165ba3d4:en-US:88f9a2dc-9cbf-434f-a243-cf2dd9f642dc:16e4e7cd:33715776:58366029:f7645509:24ee1bba:f46195d3:c128760b:19620875:874f8ea2:b2e06756:92fe8ea0:fa31b949:4877f69a:490a9d4e'

        payload = {
            'ScriptManager1_TSM': tsm_value,
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': hidden_fields['__VIEWSTATE'],
            '__VIEWSTATEGENERATOR': hidden_fields['__VIEWSTATEGENERATOR'],
            '__EVENTVALIDATION': hidden_fields['__EVENTVALIDATION'],
            'PageNum': '',
            'SortBy': 'PARID',
            'SortDir': ' asc',
            'PageSize': '15',
            'hdAction': 'Search',
            'hdIndex': '',
            'sIndex': '-1',
            'hdListType': 'PA',
            'hdJur': '',
            'hdSelectAllChecked': 'false',
            'inpParid': '',
            'inpAltid': '',
            'inpLegal3': '',
            'inpSubDiv': '',
            'inpPermit': '',
            'inpOwnerNo': '',
            'inpBook': '',
            'inpBookPage': '',
            'inpNo': street_num,
            'inpStreet': street_name,
            'inpLegal1': '',
            'inpSuf': '',
            'inpDir': '',
            'inpUnit': '-Unit-',
            'inpZip': '',
            'searchClt$hdSelSuf': '',
            'searchClt$hdSelDir': '',
            'hdTaxYear': '',
            'selSortBy': 'PARID',
            'selSortDir': ' asc',
            'selPageSize': '15',
            'searchOptions$hdBeta': '',
            'btSearch': '',
            'RadWindow_NavigateUrl_ClientState': '',
            'mode': 'REALPROP',
            'mask': '',
            'param1': '',
            'searchimmediate': ''
        }

        print(f"Step 2: Searching for {street_num} {street_name}...")
        post_response = self.scraper.post(self.BASE_URL, data=payload, headers=self.headers)
        result_soup = BeautifulSoup(post_response.text, 'html.parser')
        
        results = []
        
        # Check for single result page
        # 1. Get Address from 'Parcel' table
        parcel_table = result_soup.find('table', id='Parcel')
        address = ""
        if parcel_table:
            for row in parcel_table.find_all('tr'):
                cells = row.find_all('td')
                if cells and "Property Address:" in cells[0].text:
                    address = " ".join(cells[1].text.split())
                    break
        
        # 2. Get Parcel ID and Owner from Header Table
        parcel_id = ""
        owner = ""
        
        parcel_id_tag = result_soup.find(string=lambda text: text is not None and "Parcel ID:" in text)
        if parcel_id_tag:
            # Extract Parcel ID
            text = parcel_id_tag.strip()
            if text.startswith("Parcel ID:"):
                parcel_id = text.replace("Parcel ID:", "").strip()
            
            # Extract Owner from the same table
            header_table = parcel_id_tag.find_parent('table')
            if header_table:
                rows = header_table.find_all('tr')
                # Find the index of the row containing Parcel ID
                pid_row_index = -1
                for i, row in enumerate(rows):
                    if "Parcel ID:" in row.get_text():
                        pid_row_index = i
                        break
                
                # Owner should be in subsequent rows
                if pid_row_index != -1 and pid_row_index + 1 < len(rows):
                    # Try the next row, or the one after if empty
                    for i in range(pid_row_index + 1, len(rows)):
                        row_text = rows[i].get_text(strip=True)
                        if row_text:
                            owner = row_text
                            break

        if parcel_id and address:
            results.append(ParcelInformation(
                parcel_id=parcel_id,
                owner=owner,
                address=address
            ))
            return results

        # Check for multiple results grid
        if not results:
            grid = result_soup.find('table', id='searchResults')
            
            if grid:
                rows = grid.find_all('tr')
                
                for row in rows:
                    cells = row.find_all('td')
                    
                    if len(cells) >= 6:
                        # Column mapping based on observation:
                        # 0: Empty/Icon
                        # 1: Parcel ID
                        # 2: Legacy ID
                        # 3: Owner
                        # 4: Mailing Address
                        # 5: Property Address
                        pid = cells[1].get_text(strip=True)
                        owner_text = cells[3].get_text(strip=True)
                        addr_text = " ".join(cells[5].get_text(strip=True).split())
                        
                        if pid:
                            results.append(ParcelInformation(
                                parcel_id=pid,
                                owner=owner_text,
                                address=addr_text
                            ))

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

    print("\n--- Crow Wing County (Single) ---")
    crow_wing_scraper = CrowWingCountyScraper()
    crow_wing_data = crow_wing_scraper.search_by_address("5997", "Jack Pine")
    print_results(crow_wing_data, "5997 Jack Pine")

    print("\n--- Crow Wing County (Multiple) ---")
    crow_wing_scraper = CrowWingCountyScraper()
    crow_wing_data = crow_wing_scraper.search_by_address("", "Jack Pine")
    print_results(crow_wing_data, "5997 Jack Pine")
