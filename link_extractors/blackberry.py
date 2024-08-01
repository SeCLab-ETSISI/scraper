import aiohttp
import asyncio
import json

async def fetch_blackberry_links(session, page_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json'
    }

    try:
        async with session.get(page_url, headers=headers) as response:
            response.raise_for_status()
            data = await response.json()
            links = []

            for item in data:
                for category in item.get('category', []):
                    if 'Research & Intelligence' in category.get('name', ''):
                        link = item.get('url')
                        if link:
                            links.append(link)
                        break
            return links
    except aiohttp.ClientError as e:
        print(f"Request error: {e}")
        return []

async def extract_links():
    page_num = 1
    all_links = []
    
    async with aiohttp.ClientSession() as session:
        while True:
            url = f"https://blogs.blackberry.com/bin/blogs?page={page_num}&category=https://blogs.blackberry.com/en/category/research-and-intelligence&locale=en"
            try:
                links = await fetch_blackberry_links(session, url)
                if not links:
                    break
                print(f"[+] Processing page {page_num}")
                all_links.extend(links)
                page_num += 1
            except Exception as e:
                print(f"[-] An unexpected error has occurred. Check the URL in the browser to see if anything has changed. {url}")
                print(str(e))
                break
    
    return all_links

extract_links.__name__ = "blackberry_extractor"

if __name__ == "__main__":
    links = asyncio.run(extract_links())
    print(f"Found {len(links)} BlackBerry URLs.")
