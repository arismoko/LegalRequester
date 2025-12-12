from Counties.Clay.scraper import ClayCountyScraper

def test_clay():
    scraper = ClayCountyScraper()
    
    print("--- Testing Address Search ---")
    # Using the address from the curl command
    results = scraper.search_by_address("101", "1 AVE NE")
    for r in results:
        print(r)
        
    if results:
        pid = results[0].parcel_id
        print(f"\n--- Testing PIN Search ({pid}) ---")
        results_pin = scraper.search_by_parcel(pid)
        for r in results_pin:
            print(r)

if __name__ == "__main__":
    test_clay()
