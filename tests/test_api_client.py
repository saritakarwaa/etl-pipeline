import os
import unittest
from unittest.mock import patch

from src.ingestion.api_client import APIClient


class APIClientTests(unittest.TestCase):
    def test_uses_default_base_url_when_env_is_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            client = APIClient(base_url=None)

        self.assertEqual(client.base_url, "https://api.coingecko.com/api/v3")


if __name__ == "__main__":
    unittest.main()
