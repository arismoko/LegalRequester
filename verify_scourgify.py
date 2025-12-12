from scourgify import normalize_address_record

def check(addr):
    try:
        norm = normalize_address_record(addr)
        print(f"'{addr}' -> {norm}")
    except Exception as e:
        print(f"'{addr}' -> Error: {e}")

check("10 Mission Road West")
check("10 Mission Rd W")
