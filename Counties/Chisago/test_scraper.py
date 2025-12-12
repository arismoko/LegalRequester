from Counties.Chisago.scraper import ChisagoCountyScraper
import logging

# Configure logging to show debug info
logging.basicConfig(level=logging.DEBUG)

def test_chisago():
    scraper = ChisagoCountyScraper()
    
    # Try the user's example: House Num 101
    print("Testing search for '101' ''...")
    results = scraper.search_by_address("101", "")
    
    print(f"Found {len(results)} results.")
    for r in results:
        print(r)
    
    # Save the last response to a file for inspection
    with open("chisago_debug.html", "w") as f:
        # We need to access the last response from the scraper session if possible,
        # but the scraper class doesn't expose it directly unless we modify it.
        # However, I added a print in the scraper to save it, let's uncomment it or add it here.
        pass

if __name__ == "__main__":
    test_chisago()
