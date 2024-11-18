import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(".env")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": "https://www.clearskysec.com/category/threat-actors/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "TE": "Trailers"
}

MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
MONGO_DATABASE = os.getenv("MONGO_DATABASE")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")
GH_TOKEN = os.getenv("GH_TOKEN")


if GH_TOKEN is None:
    raise ValueError("[-] GitHub token (GH_TOKEN) not found in .env")

ORKL_API_URL = 'https://orkl.eu/api/v1/library/entries'
SCRAPING_TIME = datetime.now().strftime("%Y/%m/%d")