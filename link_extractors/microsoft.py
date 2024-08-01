import aiohttp
import asyncio
from bs4 import BeautifulSoup
import logging

async def fetch_links(session, page_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        async with session.get(page_url, headers=headers) as response:
            response.raise_for_status()
            content = await response.read()
            soup = BeautifulSoup(content, 'html.parser')
            links = []
            
            for article in soup.find_all('article'):
                a_tag = article.find('a', class_='cta')
                if a_tag and 'href' in a_tag.attrs:
                    links.append(a_tag['href'])
            return links
    except aiohttp.ClientError as e:
        logging.error(f"Request error: {e}")
        return []

async def extract_links():
    logging.debug("Starting microsoft.extract_links")
    base_url = 'https://www.microsoft.com/en-us/security/blog/?date=any&sort-by=newest-oldest&threat-intelligence[]=threat-actors'
    all_links = []
    page = 1
    async with aiohttp.ClientSession() as session:
        while True:
            page_url = f"{base_url}&page={page}"
            logging.debug(f"Fetching page {page}...")
            links = await fetch_links(session, page_url)
            if not links:
                break
            all_links.extend(links)
            page += 1
    logging.debug(f"microsoft.extract_links found {len(all_links)} links")
    return all_links

extract_links.__name__ = "microsoft_extractor"

if __name__ == "__main__":
    links = asyncio.run(extract_links())
    print(f"Found {len(links)} links.")
