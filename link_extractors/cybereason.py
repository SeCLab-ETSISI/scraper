import aiohttp
import asyncio
from bs4 import BeautifulSoup

async def fetch_page(session, url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    async with session.get(url, headers=headers) as response:
        response.raise_for_status()
        return await response.text()

async def fetch_links_from_page(session, url):
    content = await fetch_page(session, url)
    soup = BeautifulSoup(content, 'html.parser')
    links = []
    divs = soup.find_all('div', class_='column is-4-fullhd is-6-desktop is-half-tablet is-full-mobile blog-listing__single-post')
    for div in divs:
        a_tags = div.find_all('a', href=True)
        for a_tag in a_tags:
            if not a_tag.find('img'):
                links.append(a_tag['href'])
    return links

async def extract_links():
    url = "https://www.cybereason.com/blog/category/research"
    async with aiohttp.ClientSession() as session:
        print(f"Fetching URL: {url}")  # Debugging print
        links = await fetch_links_from_page(session, url)
        return links

extract_links.__name__ = "cybereason_extractor"

if __name__ == "__main__":
    links = asyncio.run(extract_links())
    print(f"Total number of links found: {len(links)}")

