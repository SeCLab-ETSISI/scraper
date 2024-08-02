import aiohttp
import asyncio
from bs4 import BeautifulSoup

async def fetch_page(session, url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    async with session.get(url, headers=headers) as response:
        if response.status == 404:
            return None
        response.raise_for_status()
        return await response.text()

async def fetch_links_from_page(session, url):
    content = await fetch_page(session, url)
    if content is None:
        return None
    soup = BeautifulSoup(content, 'html.parser')
    links = []
    divs = soup.find_all('div', class_='box col-margin relative')
    for div in divs:
        a_tag = div.find('a', href=True)
        if a_tag:
            links.append(a_tag['href'])
    return links

async def extract_links():
    base_url = "https://research.checkpoint.com/latest-publications/page/"
    async with aiohttp.ClientSession() as session:
        all_links = []
        page_num = 1

        while True:
            url = f"{base_url}{page_num}"
            print(f"Fetching URL: {url}")  # Debugging print
            links = await fetch_links_from_page(session, url)
            if links is None or not links:
                break
            all_links.extend(links)
            page_num += 1
        
        return all_links

extract_links.__name__ = "research_checkpoint_extractor"

if __name__ == "__main__":
    links = asyncio.run(extract_links())
    print(f"Total number of links found: {len(links)}")

