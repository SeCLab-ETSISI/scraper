# WIP: robots.txt complciations

"""import requests
from bs4 import BeautifulSoup
import logging

def fetch_links(page_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(page_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        links = []
        
        for article in soup.find_all('article'):
            a_tag = article.find('a', class_='cta')
            if a_tag and 'href' in a_tag.attrs:
                links.append(a_tag['href'])
        logging.debug(f"Fetched {len(links)} links from {page_url}")
        return links
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")
        return []

def fetch_all_links(base_url):
    all_links = []
    page = 1
    while True:
        page_url = f"{base_url}&page={page}"
        logging.debug(f"Fetching page {page_url}...")
        links = fetch_links(page_url)
        if not links:
            break
        all_links.extend(links)
        page += 1
    logging.debug(f"Total links fetched: {len(all_links)}")
    return all_links

def extract_links():
    base_url = 'https://www.clearskysec.com/blog/'
    return fetch_all_links(base_url)

if __name__ == "__main__":
    links = extract_links()
    print(f"Found {len(links)} links.")
"""