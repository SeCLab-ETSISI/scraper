<<<<<<< HEAD
import time
import random
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

def fetch_clearskysec_links(page_url):
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-blink-features=AutomationControlled')

    driver = uc.Chrome(options=options)
    
    try:
        driver.get(page_url)
        print(f"Fetching {page_url} - Page title: {driver.title}")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        links = []

        for article in soup.find_all('article', class_='post'):
            a_tag = article.find('a', rel='bookmark')
            if a_tag and 'href' in a_tag.attrs:
                links.append(a_tag['href'])
            else:
                print(f"No link found in article: {article}")
        driver.quit()
        return links
    except Exception as e:
        print(f"Request error: {e}")
        driver.quit()
        return []

def fetch_all_clearskysec_links(base_url):
    all_links = []
    page = 1
    while True:
        page_url = f"{base_url}/page/{page}/"
        print(f"Fetching page {page}...")
        links = fetch_clearskysec_links(page_url)
        if not links:
            break
        all_links.extend(links)
        page += 1
        time.sleep(random.uniform(3, 17))  # Sleep to mimic human browsing
    return all_links

if __name__ == "__main__":
    CLEARSKYSEC_URL_BASE = "https://www.clearskysec.com/blog"
    links = fetch_all_clearskysec_links(CLEARSKYSEC_URL_BASE)
    print(f"Found {len(links)} ClearSkySec URLs.")

=======
import re
import requests
from bs4 import BeautifulSoup
from typing import List

def valid_url(url: str) -> bool:
    """
    Check if a URL is valid based on specific criteria.

    :param url: The URL to validate.
    :return: True if the URL is valid, False otherwise.
    """
    pattern = re.compile(
        r"^https://www\.clearskysec\.com/(?!company/|solutions/|blog/|partners/|contact-us/|feed/)[^/]+/[^/]+/$"
    )
    return bool(pattern.match(url))

def extract_links() -> List[str]:
    """
    Extract all valid links from the ClearSkySec blog page.

    :return: A list of valid URLs.
    """
    url = "https://www.clearskysec.com/blog/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        print("Fetched content successfully")  # Debug statement
    except requests.RequestException as e:
        print(f"[-] Error fetching the URL: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    print("Parsing content...")  # Debug statement

    links = [a_tag.get('href') for a_tag in soup.find_all('a') if a_tag.get('href') and valid_url(a_tag.get('href'))]
    if links:
        print("Found links:")  # Debug statement
        for link in links:
            print(link)
    else:
        print("No valid links found")  # Debug statement
    return links

# Example usage
if __name__ == "__main__":
    extract_links()
>>>>>>> da0da84b842302d40514ef4e9856d32896efa675
