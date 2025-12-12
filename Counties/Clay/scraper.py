import requests
import re
from Counties.BaseScraper import CountyScraper
from Counties.models import ParcelInformation

class ClayCountyScraper(CountyScraper):
    GEOCODER_URL = "https://arcgis.claycountymn.gov/arcgis/rest/services/ArcGISOnline/ClayCounty_Geocoder/GeocodeServer/findAddressCandidates"
    PARCEL_LAYER_URL = "https://arcgis.claycountymn.gov/arcgis/rest/services/ArcGISOnline/Parcels_NoScaleRange/MapServer/0/query"

    def __init__(self):
        super().__init__()
        self.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0',
            'Referer': 'https://gis.claycountymn.gov/',
            'Origin': 'https://gis.claycountymn.gov'
        })

    def _clean_address(self, address):
        # Remove ordinal suffixes (1ST -> 1, 2ND -> 2, etc.)
        # Match number followed by ST, ND, RD, TH at word boundary, case insensitive
        return re.sub(r'\b(\d+)(?:ST|ND|RD|TH)\b', r'\1', address, flags=re.IGNORECASE)

    def search_by_address(self, street_num, street_name):
        full_address = f"{street_num} {street_name}"
        
        # Clean address for Clay County (remove ordinals)
        clean_address = self._clean_address(full_address)
        
        print(f"Geocoding address: {clean_address} (Original: {full_address})...")
        
        # Step 1: Geocode
        geo_params = {
            "SingleLine": clean_address,
            "maxLocations": 1,
            "outFields": "*",
            "outSR": '{"wkid":4326}',
            "f": "json"
        }
        
        try:
            geo_resp = self.scraper.get(self.GEOCODER_URL, params=geo_params, headers=self.headers)
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
        except Exception as e:
            print(f"Error geocoding: {e}")
            return []

        candidates = geo_data.get('candidates', [])
        if not candidates:
            print("No geocoding candidates found.")
            return []
            
        candidate = candidates[0]
        location = candidate.get('location')
        if not location:
            print("No location in geocode result.")
            return []
            
        x, y = location['x'], location['y']
        print(f"Found location: {x}, {y}. Querying parcel layer...")
        
        # Step 2: Query Parcel Layer by Geometry
        query_params = {
            "geometry": f"{x},{y}",
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "inSR": "4326",
            "outFields": "*",
            "returnGeometry": "false",
            "f": "json"
        }
        
        try:
            query_resp = self.scraper.get(self.PARCEL_LAYER_URL, params=query_params, headers=self.headers)
            query_resp.raise_for_status()
            query_data = query_resp.json()
        except Exception as e:
            print(f"Error querying parcel layer: {e}")
            return []
            
        features = query_data.get('features', [])
        results = []
        
        for feature in features:
            attrs = feature.get('attributes', {})
            
            # Extract fields
            # Note: Field names might have prefixes like "GIS.TaxParcels_with_TaxData."
            # We should handle both prefixed and non-prefixed just in case, or strip prefixes.
            
            def get_attr(name):
                # Try exact match
                if name in attrs: return attrs[name]
                # Try with prefix
                prefix = "GIS.TaxParcels_with_TaxData."
                if prefix + name in attrs: return attrs[prefix + name]
                # Try alternate prefix
                prefix2 = "GIS.TAX_PARCEL_DATA."
                if prefix2 + name in attrs: return attrs[prefix2 + name]
                return None

            pin = get_attr("PIN")
            owner = get_attr("TAX_NAME")
            
            # Construct address from components
            bldg_num = get_attr("BLDG_NUM") or ""
            street = get_attr("STREETNAME") or ""
            st_type = get_attr("STREETTYPE") or ""
            suffix = get_attr("SUFFIX_DIR") or ""
            city = get_attr("CITY") or ""
            state = get_attr("STATE") or ""
            zip_code = get_attr("ZIP") or ""
            
            # Clean up None values
            parts = [p for p in [bldg_num, street, st_type, suffix] if p]
            addr_line1 = " ".join(parts)
            
            parts2 = [p for p in [city, state, zip_code] if p]
            addr_line2 = " ".join(parts2)
            
            full_addr = f"{addr_line1}, {addr_line2}" if addr_line2 else addr_line1
            
            if pin:
                results.append(ParcelInformation(
                    parcel_id=str(pin),
                    owner=owner,
                    address=full_addr
                ))
                
        return results

    def search_by_parcel(self, parcel_id):
        print(f"Searching for PIN: {parcel_id}...")
        
        # Query Parcel Layer by PIN
        # Need to check if PIN is string or number in the query.
        # Based on field info: Name: GIS.TaxParcels_with_TaxData.PIN, Alias: PIN, Type: esriFieldTypeString
        # So we should quote it.
        
        where_clause = f"GIS.TaxParcels_with_TaxData.PIN = '{parcel_id}'"
        
        query_params = {
            "where": where_clause,
            "outFields": "*",
            "returnGeometry": "false",
            "f": "json"
        }
        
        try:
            query_resp = self.scraper.get(self.PARCEL_LAYER_URL, params=query_params, headers=self.headers)
            query_resp.raise_for_status()
            query_data = query_resp.json()
        except Exception as e:
            print(f"Error querying parcel layer: {e}")
            return []
            
        features = query_data.get('features', [])
        results = []
        
        for feature in features:
            attrs = feature.get('attributes', {})
            
            def get_attr(name):
                if name in attrs: return attrs[name]
                prefix = "GIS.TaxParcels_with_TaxData."
                if prefix + name in attrs: return attrs[prefix + name]
                prefix2 = "GIS.TAX_PARCEL_DATA."
                if prefix2 + name in attrs: return attrs[prefix2 + name]
                return None

            pin = get_attr("PIN")
            owner = get_attr("TAX_NAME")
            
            bldg_num = get_attr("BLDG_NUM") or ""
            street = get_attr("STREETNAME") or ""
            st_type = get_attr("STREETTYPE") or ""
            suffix = get_attr("SUFFIX_DIR") or ""
            city = get_attr("CITY") or ""
            state = get_attr("STATE") or ""
            zip_code = get_attr("ZIP") or ""
            
            parts = [p for p in [bldg_num, street, st_type, suffix] if p]
            addr_line1 = " ".join(parts)
            parts2 = [p for p in [city, state, zip_code] if p]
            addr_line2 = " ".join(parts2)
            full_addr = f"{addr_line1}, {addr_line2}" if addr_line2 else addr_line1
            
            if pin:
                results.append(ParcelInformation(
                    parcel_id=str(pin),
                    owner=owner,
                    address=full_addr
                ))
                
        return results
