import aiohttp
import asyncio
from bs4 import BeautifulSoup

async def fetch_page(session, url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.text()
    except aiohttp.ClientResponseError as e:
        if e.status == 404:
            print(f"Page not found: {url}")
        else:
            print(f"Error fetching page {url}: {e}")
        return None

async def fetch_links_from_page(session, url):
    content = await fetch_page(session, url)
    if content is None:
        return []
    soup = BeautifulSoup(content, 'html.parser')
    links = []
    a_tags = soup.find_all('a', class_='title', href=True)
    for a_tag in a_tags:
        links.append(a_tag['href'])
    return links

async def extract_links(base_url='https://www.sentinelone.com/labs/category/advanced-persistent-threat/page/'):
    all_links = []
    page_num = 1

    async with aiohttp.ClientSession() as session:
        while True:
            page_url = f"{base_url}{page_num}/"
            print(f"Fetching URL: {page_url}")  # Debugging print
            links = await fetch_links_from_page(session, page_url)
            if not links:
                break
            all_links.extend(links)
            page_num += 1
    
    return all_links

extract_links.__name__ = "sentinelone_extractor"

if __name__ == "__main__":
    links = asyncio.run(extract_links())
    print(f"Total number of links found: {len(links)}")
