from bs4 import BeautifulSoup
from Counties.BaseScraper import CountyScraper
from Counties.models import ParcelInformation

class AnokaCountyScraper(CountyScraper):
    BASE_URL = "https://prtpublicweb.co.anoka.mn.us/search/CommonSearch.aspx?mode=COMBINED"

    def __init__(self):
        super().__init__()
        self.headers['Origin'] = 'https://prtpublicweb.co.anoka.mn.us'
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

        payload = {
            'ScriptManager1_TSM': ';;AjaxControlToolkit, Version=4.1.50731.0, Culture=neutral, PublicKeyToken=28f01b0e84b6d53e:en-US:f8fb2a65-e23a-483b-b20e-6db6ef539a22:ea597d4b:b25378d2;Telerik.Web.UI, Version=2022.2.622.45, Culture=neutral, PublicKeyToken=121fae78165ba3d4:en-US:632d5171-8657-40d1-a04f-15afaaf31752:16e4e7cd:33715776:58366029:f7645509:24ee1bba:f46195d3:c128760b:874f8ea2:b2e06756:92fe8ea0:4877f69a:fa31b949:19620875:490a9d4e',
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': hidden_fields['__VIEWSTATE'],
            '__VIEWSTATEGENERATOR': hidden_fields['__VIEWSTATEGENERATOR'],
            '__EVENTVALIDATION': hidden_fields['__EVENTVALIDATION'],
            'PageNum': '1',
            'SortBy': 'PARID',
            'SortDir': ' asc',
            'PageSize': '15',
            'hdAction': 'Search',
            'hdIndex': '1',
            'sIndex': '-1',
            'hdListType': 'PA',
            'hdJur': '',
            'hdSelectAllChecked': 'false',
            'inpParid': '',
            'inpNumber': street_num,
            'inpStreet': street_name,
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
            'mode': 'COMBINED',
            'mask': '',
            'param1': '',
            'searchimmediate': ''
        }

        print(f"Step 2: Searching for {street_num} {street_name}...")
        post_response = self.scraper.post(self.BASE_URL, data=payload, headers=self.headers)
        result_soup = BeautifulSoup(post_response.text, 'html.parser')
        
        results = []
        
        owner_table = result_soup.find('table', id='Current Owner')
        parcel_table = result_soup.find('table', id='Parcel')
        
        if owner_table and parcel_table:
            owner = ""
            address = ""
            parcel_id = ""

            for row in owner_table.find_all('tr'):
                cells = row.find_all('td')
                if cells and "Name:" in cells[0].text:
                    owner = cells[1].text.strip()
                    break
            
            for row in parcel_table.find_all('tr'):
                cells = row.find_all('td')
                if cells and "Property Address:" in cells[0].text:
                    address = cells[1].text.strip()
                    break

            for td in result_soup.find_all('td'):
                txt = td.text.strip()
                if txt.startswith("PARID:") and len(txt) < 50:
                    parcel_id = txt.replace("PARID:", "").strip()
                    break
            
            if parcel_id:
                results.append(ParcelInformation(
                    parcel_id=parcel_id,
                    owner=owner,
                    address=address
                ))
                return results

        if not results:
            grid = result_soup.find('table', id='searchResults')
            
            if grid:
                rows = grid.find_all('tr')
                
                for row in rows[1:]:
                    cells = row.find_all('td')
                    
                    if len(cells) >= 3:
                        pid = cells[0].get_text(strip=True)
                        owner = cells[1].get_text(strip=True)
                        address = cells[2].get_text(strip=True)
                        
                        if pid:
                            results.append(ParcelInformation(
                                parcel_id=pid,
                                owner=owner,
                                address=address
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

    print("\n--- Anoka County (Single) ---")
    anoka_scraper = AnokaCountyScraper()
    anoka_data = anoka_scraper.search_by_address("4333", "117th")
    print_results(anoka_data, "4333 117th")

    print("\n--- Anoka County (Multiple) ---")
    anoka_data = anoka_scraper.search_by_address("", "117th")
    print_results(anoka_data, "117th")
