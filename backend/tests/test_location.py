import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import URLError

from app.location import get_address_from_coordinates


def json_response(payload):
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
    return response


class LocationTestCase(unittest.TestCase):
    @patch("app.location.urlopen")
    def test_uses_nominatim_result_when_available(self, urlopen):
        urlopen.return_value = json_response(
            {
                "address": {
                    "town": "Chintamani",
                    "state": "Karnataka",
                    "postcode": "563125",
                },
                "display_name": "Chintamani, Karnataka, 563125, India",
            }
        )

        location = get_address_from_coordinates(13.4, 78.05)

        self.assertEqual(location["city"], "Chintamani")
        self.assertEqual(location["pin_code"], "563125")
        self.assertEqual(urlopen.call_count, 1)

    @patch("app.location.urlopen")
    def test_falls_back_when_nominatim_is_unavailable(self, urlopen):
        urlopen.side_effect = [
            URLError("provider unavailable"),
            json_response(
                {
                    "city": "Chintamani",
                    "locality": "Chintamani",
                    "principalSubdivision": "Karnataka",
                    "postcode": "563125",
                }
            ),
        ]

        location = get_address_from_coordinates(13.4, 78.05)

        self.assertEqual(
            location,
            {
                "city": "Chintamani",
                "state": "Karnataka",
                "pin_code": "563125",
                "full_address": "Chintamani, Karnataka, 563125",
            },
        )
        self.assertIn("bigdatacloud.net", urlopen.call_args_list[1].args[0].full_url)

    @patch("app.location.urlopen", side_effect=URLError("all providers unavailable"))
    def test_returns_none_when_all_providers_are_unavailable(self, urlopen):
        self.assertIsNone(get_address_from_coordinates(13.4, 78.05))
        self.assertEqual(urlopen.call_count, 2)


if __name__ == "__main__":
    unittest.main()
