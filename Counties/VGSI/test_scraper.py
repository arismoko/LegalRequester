from .scraper import VGSIScraper

def test_scraper():
    print("Initializing VGSIScraper for Bloomington, MN...")
    try:
        scraper = VGSIScraper("Minnesota", "Bloomington")
    except Exception as e:
        print(f"Initialization failed: {e}")
        return

    print("\nTesting search_by_address('10', 'Mission Rd')...")
    results = scraper.search_by_address("10", "Mission Rd")
    print(f"Found {len(results)} results.")
    for res in results:
        print(res)

    print("\nTesting search_by_parcel('27633')...")
    results = scraper.search_by_parcel("27633")
    print(f"Found {len(results)} results.")
    for res in results:
        print(res)

if __name__ == "__main__":
    test_scraper()
