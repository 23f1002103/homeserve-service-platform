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
