import pickle
import os
import sys
import requests
from bs4 import BeautifulSoup

SECURELIST_URL_BASE = "https://securelist.com/category/apt-reports/"
SECURELIST_PAGE = "page/1/?securelist-2020-ajax=false"

def get_securelist_urls(url) -> list:
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        links = soup.find_all("a", class_="c-card__link")
        urls = [link["href"] for link in links]
    else:
        urls = None
    return urls
page = 1 
urls = []
result = []

while True:
    url_page = f"page/{page}/?securelist-2020-ajax=false" 
    securelist_url = SECURELIST_URL_BASE + url_page
    result = get_securelist_urls(securelist_url)

    if result is None:
        break
    print(f"\t [+] Successfully retrieved {len(result)} URLs from page {page}")
    page += 1
    urls += result
urls = list(set(urls)) # Extracts 300 urls of reports.