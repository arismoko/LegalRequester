import requests
from bs4 import BeautifulSoup
import json
import os
from Counties.models import ParcelInformation

class ActDataScoutScraper:
    BASE_URL = "https://www.actdatascout.com"
    SEARCH_URL = "https://www.actdatascout.com/RealProperty/Search"
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'DNT': '1',
        'Sec-GPC': '1',
        'Priority': 'u=0, i'
    }

    def __init__(self, county, state):
        self.county = county
        self.state = state
        self.county_id = self._get_county_id(county, state)
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    @staticmethod
    def is_supported(county, state):
        cache_file = os.path.join(os.path.dirname(__file__), 'counties.json')
        if not os.path.exists(cache_file):
            return False
        
        # Normalize county name
        clean_county = county.replace(" County", "").replace(" Parish", "").strip()
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                return state in data and clean_county in data[state]
        except:
            return False

    @staticmethod
    def update_data():
        from .update_counties import update_counties
        update_counties()

    def _get_county_id(self, county, state):
        cache_file = os.path.join(os.path.dirname(__file__), 'counties.json')
        
        # Normalize county name
        clean_county = county.replace(" County", "").replace(" Parish", "").strip()
        
        with open(cache_file, 'r') as f:
            data = json.load(f)
            return data.get(state, {}).get(clean_county)

    def search_by_address(self, house_num, street_name):
        if not self.county_id:
            print(f"County ID not found for {self.county}, {self.state}")
            return []

        # print(f"Step 1: Initializing session for {self.county} (ID: {self.county_id})...")
        
        # 0. Visit the county page to establish session context
        self.county_page_url = f"{self.BASE_URL}/RealProperty/{self.state}/{self.county.replace(' County', '').replace(' Parish', '')}"
        try:
            self.session.get(self.county_page_url)
        except:
            pass

        # 1. Visit the search page to get cookies and token
        # We use the BaseSearch URL to initialize the session
        init_url = f"{self.BASE_URL}/BaseSearch/Search?countyId={self.county_id}&dataType=1"
        try:
            resp = self.session.get(init_url)
            if resp.status_code != 200:
                print(f"Failed to load search page: {resp.status_code}")
                return []
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            token_input = soup.find('input', {'name': '__RequestVerificationToken'})
            if not token_input:
                print("Could not find RequestVerificationToken")
                return []
            
            token = token_input['value']
            # print(f"  Got token: {token[:10]}...")
            # print(f"  Cookies: {self.session.cookies.get_dict()}")
            
            # 2. Perform the search
            # print(f"Step 2: Searching for {house_num} {street_name}...")
            
            # Prepare search variants
            search_variants = []
            
            # Variant 1: As provided
            search_variants.append({
                'StreetNumber': house_num,
                'StreetDirection': '',
                'StreetName': street_name,
                'StreetNameMatchType': 'false' # Likely "Exact Match" = false
            })
            
            # Variant 2: Parse direction (e.g. "S Main St" -> Dir="S", Name="Main St")
            parts = street_name.split()
            if parts and parts[0].upper() in ['N', 'S', 'E', 'W', 'NORTH', 'SOUTH', 'EAST', 'WEST']:
                direction = parts[0].upper()[0]
                clean_name = ' '.join(parts[1:])
                search_variants.append({
                    'StreetNumber': house_num,
                    'StreetDirection': direction,
                    'StreetName': clean_name,
                    'StreetNameMatchType': 'false'
                })
                
            # Variant 3: Try "Contains" match (if supported, or just broader search)
            # Some systems use different values for MatchType. 
            # Let's try just the street name without direction in the name field
            if parts and parts[0].upper() in ['N', 'S', 'E', 'W']:
                 search_variants.append({
                    'StreetNumber': house_num,
                    'StreetDirection': '',
                    'StreetName': ' '.join(parts[1:]), # "Main St"
                    'StreetNameMatchType': 'false'
                })

            # Update headers for AJAX request
            # county_page_url = f"{self.BASE_URL}/RealProperty/{self.state}/{self.county.replace(' County', '').replace(' Parish', '')}"
            
            post_headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': self.BASE_URL,
                'Referer': self.county_page_url,
                'Accept': '*/*',
                'Upgrade-Insecure-Requests': None
            }
            
            final_headers = dict(self.session.headers)
            final_headers.update(post_headers)
            if 'Upgrade-Insecure-Requests' in final_headers:
                del final_headers['Upgrade-Insecure-Requests']

            for i, variant in enumerate(search_variants):
                # print(f"    Attempt {i+1}: {variant}")
                
                payload = {
                    '__RequestVerificationToken': token,
                    'CountyId': self.county_id,
                    'TaxYear': '',
                    'StreetNumber': variant['StreetNumber'],
                    'StreetDirection': variant['StreetDirection'],
                    'StreetName': variant['StreetName'],
                    'StreetNameMatchType': variant['StreetNameMatchType'],
                    'SearchType': 'address'
                }
                
                try:
                    search_resp = self.session.post(self.SEARCH_URL, data=payload, headers=final_headers)
                    
                    if search_resp.status_code != 200:
                        print(f"    Search failed: {search_resp.status_code}")
                        continue
                    
                    results = self._parse_results(search_resp.content)
                    if results:
                        # print(f"    -> Found {len(results)} results!")
                        return results
                    # else:
                        # print("    -> No results.")
                        
                except Exception as e:
                    print(f"    Error in attempt {i+1}: {e}")
            
            return []

        except Exception as e:
            print(f"Error searching ActDataScout: {e}")
            return []

    def _parse_results(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        results = []
        
        table = soup.find('table')
        if table:
            # Try to identify columns by header
            headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
            # print(f"DEBUG: Table headers: {headers}")
            
            # Default indices (assuming standard layout if no headers)
            # Often: Actions | Parcel | Owner | Address | ...
            idx_parcel = 1
            idx_owner = 2
            idx_address = 3
            
            # Map headers if possible
            if headers:
                idx_parcel = -1
                idx_owner = -1
                idx_address = -1
                
                for i, h in enumerate(headers):
                    if 'parcel' in h: idx_parcel = i
                    elif 'owner' in h: idx_owner = i
                    elif 'address' in h or 'location' in h: idx_address = i
                
                # If we couldn't find them, revert to defaults or guess
                if idx_parcel == -1: idx_parcel = 1
                if idx_owner == -1: idx_owner = 2
                if idx_address == -1: idx_address = 3

            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if not cols: continue
                
                # Skip if not enough columns
                if len(cols) <= max(idx_parcel, idx_owner, idx_address):
                    continue
                    
                p_id = cols[idx_parcel].get_text(strip=True)
                own = cols[idx_owner].get_text(strip=True)
                addr = cols[idx_address].get_text(strip=True)
                
                # Extract link from Parcel ID column or any column
                link = cols[idx_parcel].find('a', href=True)
                if not link:
                    link = row.find('a', href=True)
                
                url = ""
                if link:
                    href = link['href']
                    if isinstance(href, list):
                        href = href[0]
                    
                    if isinstance(href, str):
                        if href.startswith('/'):
                            url = f"{self.BASE_URL}{href}"
                        else:
                            url = href

                results.append(ParcelInformation(
                    parcel_id=p_id,
                    owner=own,
                    address=addr,
                    county_url=str(url) if url else self.county_page_url
                ))

        return results
