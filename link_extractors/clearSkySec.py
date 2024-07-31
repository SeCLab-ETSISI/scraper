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

