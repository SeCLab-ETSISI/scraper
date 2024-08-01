import aiohttp
import asyncio
from bs4 import BeautifulSoup

async def fetch_securelist_links(session, page_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        async with session.get(page_url, headers=headers) as response:
            response.raise_for_status()
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            links = []

            for article in soup.find_all('article', class_='c-card'):
                a_tag = article.find('a', class_='c-card__link')
                if a_tag and 'href' in a_tag.attrs:
                    links.append(a_tag['href'])
            return links
    except aiohttp.ClientError as e:
        print(f"Finishing due to request error: {e}")
        return []

async def extract_links():
    base_url = "https://securelist.com/category/apt-reports/page/"
    page_num = 1
    all_links = []

    async with aiohttp.ClientSession() as session:
        while True:
            page_url = f"{base_url}{page_num}/?securelist-2020-ajax=false"
            print(f"Fetching page {page_num}...")
            links = await fetch_securelist_links(session, page_url)
            if not links:
                break
            all_links.extend(links)
            page_num += 1
    
    return all_links

extract_links.__name__ = "securelist_extractor"

if __name__ == "__main__":
    links = asyncio.run(extract_links())
    print(f"Found {len(links)} links.")
