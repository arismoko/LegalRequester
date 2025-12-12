from abc import ABC, abstractmethod
import cloudscraper

class CountyScraper(ABC):
    """
    Abstract base class defining the interface for county scrapers.
    Implements the Strategy Pattern.
    """
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
            'Sec-GPC': '1',
            'Priority': 'u=0, i'
        }

    def _get_hidden_fields(self, soup):
        """Helper to extract ASP.NET hidden fields."""
        def get_val(name):
            tag = soup.find('input', {'name': name})
            return tag.get('value', '') if tag else ''
        
        return {
            '__VIEWSTATE': get_val('__VIEWSTATE'),
            '__VIEWSTATEGENERATOR': get_val('__VIEWSTATEGENERATOR'),
            '__EVENTVALIDATION': get_val('__EVENTVALIDATION'),
        }

    @abstractmethod
    def search_by_address(self, street_num, street_name):
        pass

    @abstractmethod
    def search_by_parcel(self, parcel_id):
        pass
