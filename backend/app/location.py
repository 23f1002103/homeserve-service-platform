"""Small helper for converting map coordinates into an address."""

import json
import math
from functools import lru_cache
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def normalize_city_name(value):
    """Make common city spellings comparable."""
    normalized = "".join(character for character in (value or "").casefold() if character.isalnum())
    aliases = {
        "bangalore": "bengaluru",
        "bangaluru": "bengaluru",
        "bangaloreurban": "bengaluru",
        "bengaluruurban": "bengaluru",
    }
    return aliases.get(normalized, normalized)


def normalize_state_name(value):
    """Normalize a state name for case- and punctuation-insensitive matching."""
    return "".join(
        character for character in (value or "").casefold() if character.isalnum()
    )


def location_matches_area(location, area):
    """Return whether a reverse-geocoded location belongs to a city service area."""
    return (
        bool(normalize_city_name(location.get("city")))
        and normalize_city_name(location.get("city")) == normalize_city_name(area.city)
        and normalize_state_name(location.get("state"))
        == normalize_state_name(area.state)
    )


def coordinates_match_area(latitude, longitude, area):
    """Return whether coordinates fall inside an area's configured circle."""
    if not area.has_geo_zone:
        return False

    earth_radius_km = 6371.0088
    lat_1 = math.radians(latitude)
    lat_2 = math.radians(area.center_latitude)
    latitude_delta = math.radians(area.center_latitude - latitude)
    longitude_delta = math.radians(area.center_longitude - longitude)
    haversine = (
        math.sin(latitude_delta / 2) ** 2
        + math.cos(lat_1)
        * math.cos(lat_2)
        * math.sin(longitude_delta / 2) ** 2
    )
    distance_km = 2 * earth_radius_km * math.asin(math.sqrt(haversine))
    return distance_km <= area.radius_km


def find_area_for_coordinates(latitude, longitude, areas):
    """Choose the smallest configured zone containing the coordinate."""
    matches = [
        area for area in areas if coordinates_match_area(latitude, longitude, area)
    ]
    return min(matches, key=lambda area: area.radius_km) if matches else None


def _request_json(url):
    """Fetch JSON without allowing a provider outage to break the request."""
    map_request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": (
                "HomeServe/1.0 "
                "(https://homeserve-service-platform.onrender.com)"
            ),
        },
    )

    try:
        with urlopen(map_request, timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None


def _nominatim_address(latitude, longitude):
    query = urlencode(
        {"format": "jsonv2", "lat": latitude, "lon": longitude, "addressdetails": 1}
    )
    result = _request_json(f"https://nominatim.openstreetmap.org/reverse?{query}")
    if not result:
        return None

    address = result.get("address", {})
    if not address:
        return None
    city = (
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("county")
        or ""
    )

    return {
        "city": city.strip(),
        "state": (address.get("state") or "").strip(),
        "pin_code": (address.get("postcode") or "").strip(),
        "full_address": (result.get("display_name") or "").strip(),
    }


@lru_cache(maxsize=128)
def search_place(query):
    """Find one Indian place for the admin's explicit map search."""
    normalized_query = (query or "").strip()
    if len(normalized_query) < 2:
        return None

    parameters = urlencode(
        {
            "q": normalized_query,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": 1,
            "countrycodes": "in",
        }
    )
    results = _request_json(f"https://nominatim.openstreetmap.org/search?{parameters}")
    if not isinstance(results, list) or not results:
        return None

    result = results[0]
    address = result.get("address", {})
    try:
        latitude = float(result["lat"])
        longitude = float(result["lon"])
    except (KeyError, TypeError, ValueError):
        return None

    city = (
        address.get("city")
        or address.get("town")
        or address.get("municipality")
        or address.get("village")
        or address.get("county")
        or ""
    )
    return {
        "latitude": latitude,
        "longitude": longitude,
        "city": city.strip(),
        "state": (address.get("state") or "").strip(),
        "display_name": (result.get("display_name") or normalized_query).strip(),
    }


def _big_data_cloud_address(latitude, longitude):
    query = urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "localityLanguage": "en",
        }
    )
    result = _request_json(
        f"https://api.bigdatacloud.net/data/reverse-geocode-client?{query}"
    )
    if not result:
        return None

    city = (result.get("city") or result.get("locality") or "").strip()
    state = (result.get("principalSubdivision") or "").strip()
    pin_code = (result.get("postcode") or "").strip()
    if not any((city, state, pin_code)):
        return None
    full_address = ", ".join(value for value in (city, state, pin_code) if value)
    return {
        "city": city,
        "state": state,
        "pin_code": pin_code,
        "full_address": full_address,
    }


def get_address_from_coordinates(latitude, longitude):
    """Reverse geocode coordinates, with a fallback if one provider is down."""
    return _nominatim_address(latitude, longitude) or _big_data_cloud_address(
        latitude, longitude
    )
