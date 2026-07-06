from src.ingestion.extractor import CoinGeckoExtractor

extractor = CoinGeckoExtractor()

data = extractor.extract()

print(
    len(data)
)

print(
    data[0]
)