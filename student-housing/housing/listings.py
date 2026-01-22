import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "listings.json"

def get_all_listings():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_all_listings(listings):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(listings, f, ensure_ascii=False, indent=2)

def add_listing(new_listing: dict):
    listings = get_all_listings()
    max_id = max([l.get("id", 0) for l in listings], default=0)
    new_listing["id"] = max_id + 1
    listings.append(new_listing)
    save_all_listings(listings)
    return new_listing
