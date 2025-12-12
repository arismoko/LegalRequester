from Counties.BeaconSchneiderCorp.scraper import BeaconSchneiderCorpCountyScraper
from Counties.Anoka.scraper import AnokaCountyScraper
from Counties.Washington.scraper import WashingtonCountyScraper
from Counties.CrowWing.scraper import CrowWingCountyScraper
from Counties.Hennepin.scraper import HennepinCountyScraper
from Counties.Clearwater.scraper import ClearwaterCountyScraper
from search import FindPropertyDetails, update_all_scraper_data

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

if __name__ == "__main__":
    print("\n--- Updating Scraper Data ---")
    update_all_scraper_data()

    print("\n--- Testing FindPropertyDetails ---")
    # Test with the requested address
    addr = "12575 IRISH AVE N"
    print(f"\nSearching for: {addr}")
    results = FindPropertyDetails(addr)
    if not results:
        print("No results found.")
    elif isinstance(results, dict):
        for key, items in results.items():
            print(f"\n--- {key} ---")
            if isinstance(items, list):
                for item in items:
                    if hasattr(item, 'to_dict'):
                        print(item.to_dict())
                    else:
                        print(item)
            else:
                print(items)
    else:
        
        for res in results:
            if hasattr(res, 'to_dict'):
                print(res.to_dict())
            else:
                print(res)


