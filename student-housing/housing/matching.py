from housing.listings import get_all_listings

def filter_by_university(universite_id: str):
    listings = get_all_listings()
    return [l for l in listings if l.get("universite") == universite_id]

def filter_by_distance(listings, max_km: float):
    return [l for l in listings if float(l.get("distance_km", 9999)) <= max_km]

def get_matches(universite_id: str, max_km: float = 3.0):
    res = filter_by_university(universite_id)
    res = filter_by_distance(res, max_km)
    # ucuzdan pahalıya
    res.sort(key=lambda x: x.get("loyer", 10**9))
    return res
