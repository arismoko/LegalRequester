import requests
from bs4 import BeautifulSoup
from Counties.BaseScraper import CountyScraper
from Counties.models import ParcelInformation

class BeltramiCountyScraper(CountyScraper):
    BASE_URL = "https://propertyportal.co.beltrami.mn.us/search/CommonSearch.aspx?mode=COMBINED"

    def __init__(self):
        super().__init__()
        self.scraper = requests.Session()
        self.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Origin': 'https://propertyportal.co.beltrami.mn.us',
            'Referer': 'https://propertyportal.co.beltrami.mn.us/search/commonsearch.aspx?mode=combined',
        })
        # Add disclaimer cookie
        self.scraper.cookies.set('DISCLAIMER', '1')

    def search_by_address(self, street_num, street_name):
        print(f"Fetching search page for Beltrami: {street_num} {street_name}")
        try:
            response = self.scraper.get(self.BASE_URL, headers=self.headers)
            response.raise_for_status()
        except Exception as e:
            print(f"Request failed: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        hidden_fields = self._get_hidden_fields(soup)
        
        if not hidden_fields.get('__VIEWSTATE'):
            print("Error: Failed to retrieve search page tokens.")
            return []

        # Strategy: If street number is provided, search by number only to avoid strict matching issues
        # Then filter results by street name if provided.
        search_num = street_num if street_num else ''
        search_street = '' if street_num else (street_name if street_name else '')

        payload = {
            'ScriptManager1_TSM': ';;AjaxControlToolkit, Version=4.1.50731.0, Culture=neutral, PublicKeyToken=28f01b0e84b6d53e:en-US:f8fb2a65-e23a-483b-b20e-6db6ef539a22:ea597d4b:b25378d2;Telerik.Web.UI, Version=2020.2.512.45, Culture=neutral, PublicKeyToken=121fae78165ba3d4:en-US:88f9a2dc-9cbf-434f-a243-cf2dd9f642dc:16e4e7cd:f7645509:24ee1bba:c128760b:19620875:874f8ea2:f46195d3:b2e06756:92fe8ea0:fa31b949:4877f69a:33715776:490a9d4e',
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': hidden_fields['__VIEWSTATE'],
            '__VIEWSTATEGENERATOR': hidden_fields.get('__VIEWSTATEGENERATOR', ''),
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
            'inpNumber': search_num,
            'inpStreet': search_street,
            'inpSuffix': '',
            'inpDirection': '',
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

        try:
            post_response = self.scraper.post(self.BASE_URL, data=payload, headers=self.headers)
            post_response.raise_for_status()
        except Exception as e:
            print(f"Search request failed: {e}")
            return []

        # Save for debugging
        with open("beltrami_result.html", "w") as f:
            f.write(post_response.text)

        result_soup = BeautifulSoup(post_response.text, 'html.parser')
        results = []

        # Find the results table
        table = result_soup.find('table', {'id': 'searchResults'})
        if not table:
            return []
            
        rows = table.find_all('tr', class_='SearchResults')
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 5:
                parcel_id = cols[0].get_text(strip=True)
                owner = cols[1].get_text(strip=True)
                address_full = cols[2].get_text(strip=True)
                city = cols[3].get_text(strip=True)
                zip_code = cols[4].get_text(strip=True)
                
                full_address = f"{address_full}, {city} {zip_code}".strip()
                
                parcel = ParcelInformation(
                    parcel_id=parcel_id,
                    address=full_address,
                    owner=owner
                )
                results.append(parcel)
        
        # Filter results if we searched by number but also have a street name
        final_results = []
        for r in results:
            if street_num and street_name:
                # Check if street name is in the address
                # Simple check: is street_name (upper) in r.address (upper)
                # We split street_name to handle cases like "2nd St" vs "2nd"
                s_name_parts = street_name.upper().split()
                addr_upper = r.address.upper()
                
                # Check if all parts of street name are in address? 
                # Or just the main part?
                # "2nd" is in "1011 2ND ST SE" -> Yes
                # "2nd St" is in "1011 2ND ST SE" -> Yes
                # "2nd Street" is NOT in "1011 2ND ST SE" -> No
                
                # Let's be lenient: check if the first part of street_name is in address
                if s_name_parts[0] in addr_upper:
                     final_results.append(r)
            else:
                final_results.append(r)
                
        return final_results

    def search_by_parcel(self, parcel_id):
        return []

