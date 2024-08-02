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

async def fetch_main_links(session, base_url):
    content = await fetch_page(session, base_url)
    soup = BeautifulSoup(content, 'html.parser')
    links = []
    a_tags = soup.find_all('a', class_='inlink', href=True)
    for a_tag in a_tags:
        links.append("https://apt.etda.or.th" + a_tag['href'])
    return links

async def fetch_external_links(session, url):
    content = await fetch_page(session, url)
    soup = BeautifulSoup(content, 'html.parser')
    links = []
    a_tags = soup.find_all('a', class_='exlink', href=True, title="Follow external link")
    for a_tag in a_tags:
        links.append(a_tag['href'])
    return links

async def extract_links():
    base_url = 'https://apt.etda.or.th/cgi-bin/listgroups.cgi'
    all_links = []

    async with aiohttp.ClientSession() as session:
        main_links = await fetch_main_links(session, base_url)
        for link in main_links:
            print(f"Fetching URL: {link}")  # Debugging print
            external_links = await fetch_external_links(session, link)
            all_links.extend(external_links)
    
    return all_links

extract_links.__name__ = "etda_extractor"

if __name__ == "__main__":
    links = asyncio.run(extract_links())
    print(f"Total number of external links found: {len(links)}")

