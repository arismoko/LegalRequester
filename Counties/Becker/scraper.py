import requests
from bs4 import BeautifulSoup
from Counties.BaseScraper import CountyScraper
from Counties.models import ParcelInformation

class BeckerCountyScraper(CountyScraper):
    BASE_URL = "https://gis-server.co.becker.mn.us/www/parcel_search.aspx"

    def __init__(self):
        super().__init__()
        # Use standard requests session
        self.scraper = requests.Session()
        self.headers.update({
            'Origin': 'https://gis-server.co.becker.mn.us',
            'Referer': self.BASE_URL,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })

    def search_by_address(self, street_num, street_name):
        try:
            response = self.scraper.get(self.BASE_URL, headers=self.headers)
        except Exception as e:
            print(f"Request failed: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        hidden_fields = self._get_hidden_fields(soup)
        if not hidden_fields['__VIEWSTATE']:
            print("Error: Failed to retrieve search page tokens.")
            return []

        # The search box seems to search specific columns (HouseNum, StreetName) 
        # but not the full address string. Searching for "105 2ND" fails.
        # So we search for the most specific single term we have.
        if street_num:
            search_term = street_num
        else:
            search_term = street_name
        
        payload = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': hidden_fields['__VIEWSTATE'],
            '__EVENTVALIDATION': hidden_fields['__EVENTVALIDATION'],
            'txtPIN': '',
            'txtOwnerName': '',
            'txtAddress': search_term,
            'btnSearchAddress': 'Search Address'
        }

        post_response = self.scraper.post(self.BASE_URL, data=payload, headers=self.headers)
        result_soup = BeautifulSoup(post_response.text, 'html.parser')
        
        results = []
        
        # Parse results from the table
        # Look for the table with id 'gvResults' or similar, or just find the table with headers
        table = result_soup.find('table', id='gvResults')
        if not table:
            # Fallback: look for table with 'Parcel' in header
            for t in result_soup.find_all('table'):
                header = t.find('th')
                if header and 'Parcel' in header.get_text():
                    table = t
                    break
        
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    # Column 1: Parcel ID
                    parcel_id_tag = cells[0].find('a')
                    parcel_id = parcel_id_tag.text.strip() if parcel_id_tag else cells[0].text.strip()
                    
                    # Column 2: Address
                    # The address cell might contain an <a> tag for the map marker, we want the text
                    address = cells[1].get_text(strip=True)
                    
                    # Column 3: Owner
                    owner = cells[2].get_text(strip=True)
                    
                    results.append(ParcelInformation(
                        parcel_id=parcel_id,
                        address=address,
                        owner=owner
                    ))
        
        # Filter results client-side if we searched by house number but have a street name
        if street_num and street_name:
            filtered_results = []
            street_name_upper = street_name.upper()
            # Simple heuristic: check if any significant part of the street name is in the address
            # Split by space, ignore common suffixes if possible, but for now just check words
            # "2ND ST NW" -> "2ND", "ST", "NW"
            # "2nd" -> "2ND"
            
            # We want to be permissive. If ANY word from street_name (longer than 1 char?) is in address?
            # Or if the whole street_name is a substring?
            # "2ND" is in "105 2ND ST NE".
            # "2nd Street" -> "2ND" is in "105 2ND ST NE". "STREET" is not (it's "ST").
            
            # Let's try to match the first word of the street name
            first_word = street_name_upper.split()[0] if street_name_upper else ""
            
            for res in results:
                if first_word and first_word in res.address.upper():
                    filtered_results.append(res)
                elif not first_word:
                    filtered_results.append(res)
            
            return filtered_results

        return results

    def search_by_parcel(self, parcel_id):
        return []
