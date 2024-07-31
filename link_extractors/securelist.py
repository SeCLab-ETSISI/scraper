import requests
from bs4 import BeautifulSoup
import time

def get_report_links():
    base_url = "https://www.secureworks.com/research?page="
    page_num = 1
    report_links = []
    max_retries = 3  # Number of retries for each page
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    while True:
        url = f"{base_url}{page_num}"
        print(f"Fetching URL: {url}")  # Debugging print
        retries = 0

        while retries < max_retries:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()  # Raise an error for bad status codes

                soup = BeautifulSoup(response.content, "html.parser")
                container = soup.find("div", class_="cards-container")
                if not container:
                    print(f"No cards container found on page {page_num}")
                    break

                cards = container.find_all("a", class_="FilterCard css-tfil0o ef3voxb0")
                print(f"Number of links found on page {page_num}: {len(cards)}")  # Debugging print

                if not cards:
                    break

                for card in cards:
                    href = card.get("href")
                    if href:
                        full_link = "https://www.secureworks.com" + href
                        print(f"Found link: {full_link}")  # Debugging print
                        report_links.append(full_link)

                page_num += 1
                break  # Exit retry loop if successful

            except requests.exceptions.RequestException as e:
                print(f"RequestException on page {page_num}, retrying ({retries + 1}/{max_retries})...")
                retries += 1
                time.sleep(2)  # Wait before retrying

            except Exception as e:
                print(f"An error occurred: {e}")
                break

        if retries == max_retries:
            print(f"Max retries reached for page {page_num}, stopping.")
            break

    return report_links

if __name__ == "__main__":
    links = get_report_links()
    print(f"Total number of links found: {len(links)}")  # Debugging print
