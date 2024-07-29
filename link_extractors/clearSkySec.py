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
