import yaml
from dotenv import load_dotenv
import os

from configs.constants import CONFIG_PATH
from src.ingestion.api_client import APIClient


load_dotenv()


class CoinGeckoExtractor:

    def __init__(self):

        with open(
            CONFIG_PATH,
            "r"
        ) as file:

            self.config = yaml.safe_load(
                file
            )

        self.client = APIClient(
            base_url=os.getenv(
                "COINGECKO_BASE_URL"
            )
        )


    def extract(self):

        api_config = self.config["api"]

        all_records = []

        for page in range(
            1,
            api_config["page_limit"] + 1
        ):

            params = {

                "vs_currency":
                api_config["currency"],

                "order":
                api_config["order"],

                "per_page":
                api_config["per_page"],

                "page":
                page
            }

            data = self.client.get(
                endpoint=api_config["endpoint"],
                params=params
            )

            all_records.extend(
                data
            )

        return all_records