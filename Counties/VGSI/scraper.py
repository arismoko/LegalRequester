import json
import os
import requests
import urllib3
from bs4 import BeautifulSoup
from scourgify import normalize_address_record
from ..BaseScraper import CountyScraper
from ..models import ParcelInformation
from .update_data import update_data

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class VGSIScraper(CountyScraper):
    def __init__(self, state, municipality):
        super().__init__()
        
        self.state = state
        self.municipality = municipality
        self.base_url = self._get_base_url(state, municipality)
        
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0',
            'Content-Type': 'application/json; charset=utf-8',
            'X-Requested-With': 'XMLHttpRequest'
        })

    def _get_base_url(self, state, municipality):
        # Load data.json
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_file = os.path.join(base_dir, 'data.json')
        
        if not os.path.exists(data_file):
            # Try to update data if not exists
            print("Data file not found. Fetching supported municipalities...")
            update_data(data_file)
            
        with open(data_file, 'r') as f:
            data = json.load(f)
            
        if state not in data:
            # Try to find case-insensitive match
            found = False
            for s in data:
                if s.lower() == state.lower():
                    state = s
                    found = True
                    break
            if not found:
                raise ValueError(f"State '{state}' not found in VGSI data.")
            
        if municipality not in data[state]:
            # Try case-insensitive match
            found = False
            for m in data[state]:
                if m.lower() == municipality.lower():
                    municipality = m
                    found = True
                    break
            if not found:
                raise ValueError(f"Municipality '{municipality}' not found in VGSI data for state '{state}'.")
            
        url = data[state][municipality]
        return url.rstrip('/')

    def update_supported_counties(self):
        """Updates the local database of supported counties/municipalities."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_file = os.path.join(base_dir, 'data.json')
        update_data(data_file)

    def _fetch_parcel_details(self, pid):
        """Fetches and parses the parcel detail page."""
        url = f"{self.base_url}/Parcel.aspx?Pid={pid}"
        try:
            # We need to remove Content-Type: application/json for GET request
            headers = dict(self.session.headers)
            if 'Content-Type' in headers:
                del headers['Content-Type']
            if 'X-Requested-With' in headers:
                del headers['X-Requested-With']
                
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract Owner
            owner_span = soup.find('span', id='MainContent_lblGenOwner')
            owner = owner_span.text.strip() if owner_span else "Unknown"
            
            # Extract Address
            address_span = soup.find('span', id='MainContent_lblLocation')
            address = address_span.text.strip() if address_span else ""
            
            city_state_zip_span = soup.find('span', id='MainContent_lblCtz')
            if city_state_zip_span:
                address += f", {city_state_zip_span.text.strip()}"
            
            # Extract Parcel ID
            # Try MainContent_lblAcctNum first (Property ID #)
            parcel_id_span = soup.find('span', id='MainContent_lblAcctNum')
            if parcel_id_span:
                parcel_id = parcel_id_span.text.strip()
            else:
                # Fallback to MBLU
                mblu_span = soup.find('span', id='MainContent_lblMblu')
                parcel_id = mblu_span.text.strip() if mblu_span else pid

            return ParcelInformation(
                parcel_id=parcel_id,
                owner=owner,
                address=address
            )

        except Exception as e:
            print(f"Error fetching details for PID {pid}: {e}")
            return None

    def search_by_address(self, street_num, street_name):
        # Normalize address using scourgify
        try:
            full_addr = f"{street_num} {street_name}"
            normalized = normalize_address_record(full_addr)
            # scourgify returns uppercase address_line_1
            search_term = normalized.get('address_line_1', full_addr).upper()
        except Exception as e:
            print(f"Error normalizing address: {e}")
            search_term = f"{street_num} {street_name}".strip().upper()

        url = f"{self.base_url}/async.asmx/GetDataAddress"
        
        # Ensure Referer is set
        self.session.headers['Referer'] = f"{self.base_url}/Search.aspx"
        
        payload = {
            "inVal": search_term,
            "src": "i_address"
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if 'd' in data:
                for item in data['d']:
                    pid = item.get('id')
                    if pid and pid != "0":
                        parcel_info = self._fetch_parcel_details(pid)
                        if parcel_info:
                            results.append(parcel_info)
            return results
            
        except Exception as e:
            print(f"Error searching by address: {e}")
            return []

    def search_by_parcel(self, parcel_id):
        url = f"{self.base_url}/async.asmx/GetData2"
        
        # Ensure Referer is set
        self.session.headers['Referer'] = f"{self.base_url}/Search.aspx"
        
        payload = {
            "inVal": parcel_id,
            "src": "i_pid"
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if 'd' in data:
                for item in data['d']:
                    pid = item.get('id')
                    if pid and pid != "0":
                        parcel_info = self._fetch_parcel_details(pid)
                        if parcel_info:
                            results.append(parcel_info)
            return results
            
        except Exception as e:
            print(f"Error searching by parcel: {e}")
            return []
