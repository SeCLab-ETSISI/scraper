import aiohttp
import asyncio
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

async def fetch_secureworks_links(session, page_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.google.com',
        'DNT': '1',  # Do Not Track Request Header
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        async with session.get(page_url, headers=headers) as response:
            response.raise_for_status()
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            report_links = []

            container = soup.find("div", class_="cards-container")
            if not container:
                logging.debug(f"No cards container found on page {page_url}")
            else:
                cards = container.find_all("a", class_="FilterCard")
                logging.debug(f"Number of cards found on page {page_url}: {len(cards)}")
                for card in cards:
                    href = card.get("href")
                    if href:
                        full_link = "https://www.secureworks.com" + href
                        logging.debug(f"Found link: {full_link}")
                        report_links.append(full_link)
            return report_links
    except aiohttp.ClientError as e:
        logging.error(f"Request error on page {page_url}: {e}")
        return []

async def extract_links():
    base_url = "https://www.secureworks.com/research?page="
    page_num = 1
    all_links = []

    async with aiohttp.ClientSession() as session:
        while True:
            page_url = f"{base_url}{page_num}"
            logging.debug(f"Fetching URL: {page_url}")
            links = await fetch_secureworks_links(session, page_url)
            if not links:
                logging.debug(f"No links found on page {page_num}, stopping.")
                break
            all_links.extend(links)
            page_num += 1
    
    return all_links

extract_links.__name__ = "secureworks_extractor"

if __name__ == "__main__":
    links = asyncio.run(extract_links())
    print(f"Total number of links found: {len(links)}")
