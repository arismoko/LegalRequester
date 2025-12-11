from Counties.Ramsey import RamseyCountyScraper
from Counties.Anoka import AnokaCountyScraper

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
    #Single Response
    print("--- Ramsey County (Single) ---")
    scraper = RamseyCountyScraper()
    # Note: The example " 2346 Belmont" might need trimming or specific handling if the scraper expects clean input
    data = scraper.search_by_address("2346", "Belmont")
    print_results(data, "2346 Belmont")

    #Multiple Responses
    print("\n--- Ramsey County (Multiple) ---")
    data = scraper.search_by_address("3150", "GLEN OAKS")
    print_results(data, "3150 GLEN OAKS")
    
    print("\n--- Anoka County (Single) ---")
    anoka_scraper = AnokaCountyScraper()
    # Using the example from the curl request: 4333 117th
    anoka_data = anoka_scraper.search_by_address("4333", "117th")
    print_results(anoka_data, "4333 117th")

    print("\n--- Anoka County (Multiple) ---")
    anoka_data = anoka_scraper.search_by_address("", "117th")
    print_results(anoka_data, "117th")