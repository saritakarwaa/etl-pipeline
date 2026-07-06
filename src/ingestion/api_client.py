import os
import time

import requests
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_fixed

from src.utils.logger import setup_logger


logger = setup_logger()


class APIClient:

    def __init__(
        self,
        base_url: str | None,
        timeout: int = 30
    ):

        self.base_url = base_url or os.getenv(
            "COINGECKO_BASE_URL",
            "https://api.coingecko.com/api/v3"
        )

        self.timeout = timeout


    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(5)
    )
    def get(
        self,
        endpoint: str,
        params: dict
    ):

        if not self.base_url:
            raise ValueError("API base URL is not configured")

        url = f"{self.base_url.rstrip('/')}{endpoint}"

        logger.info(
            f"Requesting {url}"
        )

        response = requests.get(
            url,
            params=params,
            timeout=self.timeout
        )

        response.raise_for_status()

        time.sleep(
            1
        )

        return response.json()