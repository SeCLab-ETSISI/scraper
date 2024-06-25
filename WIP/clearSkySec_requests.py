import re
import requests
from bs4 import BeautifulSoup
import random
import time

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15"
]

HEADERS = {
    "User-Agent": random.choice(USER_AGENTS),
    "Referer": "https://www.clearskysec.com/category/threat-actors/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "TE": "Trailers"
}

# proxies from https://geonode.com/free-proxy-list
PROXIES = [
    {"http": "http://209.127.191.180:80", "https": "https://209.127.191.180:80"},
    {"http": "http://103.105.49.53:80", "https": "https://103.105.49.53:80"},
    {"http": "http://103.78.141.164:80", "https": "https://103.78.141.164:80"},
    {"http": "http://157.245.207.186:8080", "https": "https://157.245.207.186:8080"},
    {"http": "http://47.241.165.133:443", "https": "https://47.241.165.133:443"}
]

def is_valid_url(url: str) -> bool:
    """
    Validates the given URL to check if it is a valid report URL and not part of excluded sections.

    Parameters:
    url (str): The URL to be validated.

    Returns:
    bool: True if the URL is a valid report URL, False otherwise.
    """
    # pattern for valid report URLs and exclusion patterns
    valid_pattern = re.compile(r'https://www\.clearskysec\.com/[^/]+/$')
    exclusion_pattern = re.compile(r'https://www\.clearskysec\.com/(disinformation|general|company|blog)/')
    
    # check if the URL matches the valid pattern and does not match the exclusion pattern
    if valid_pattern.match(url) and not exclusion_pattern.match(url):
        return True
    return False

def extract_and_validate_links(url: str) -> list:
    """
    Extracts all 'a href' links from the given URL and validates them using the is_valid_url function.

    Parameters:
    url (str): The URL to scrape for links.

    Returns:
    list: A list of valid URLs.
    """
    valid_urls = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for proxy in PROXIES:
        retries = 3
        for attempt in range(retries):
            try:
                session.proxies.update(proxy)
                response = session.get(url, timeout=20)
                print(f"Status Code: {response.status_code} with Proxy: {proxy}")

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    a_tags = soup.find_all('a', href=True)
                    print(len(a_tags))

                    for tag in a_tags:
                        href = tag['href']
                        if is_valid_url(href):
                            valid_urls.append(href)
                    return valid_urls
                else:
                    print("Failed to retrieve the page.")
                    break
            except requests.exceptions.RequestException as e:
                print(f"Error with Proxy {proxy}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # exponential backoff
                else:
                    break
    return valid_urls

url_to_scrape = 'https://www.clearskysec.com/category/threat-actors/'

valid_links = extract_and_validate_links(url_to_scrape)
print(valid_links)
