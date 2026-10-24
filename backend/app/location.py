"""Small helper for converting map coordinates into an address."""

import json
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


def get_address_from_coordinates(latitude, longitude):
    """Ask OpenStreetMap for the address at the given coordinates."""
    query = urlencode(
        {"format": "jsonv2", "lat": latitude, "lon": longitude, "addressdetails": 1}
    )
    map_request = Request(
        f"https://nominatim.openstreetmap.org/reverse?{query}",
        headers={"User-Agent": "HomeServe-college-project/1.0"},
    )

    try:
        with urlopen(map_request, timeout=8) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None

    address = result.get("address", {})
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
