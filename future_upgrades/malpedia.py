import requests
from bs4 import BeautifulSoup

def get_report_links():
    base_url = "https://malpedia.caad.fkie.fraunhofer.de/library/"
    page_num = 1
    report_links = []

    while True:                     # i really hate doing this but i don't think there's a much better way in python
        # print(f"Processing page {page_num}")
        url = f"{base_url}{page_num}"
        response = requests.get(url)
        if response.status_code != 200:
            break
        
        soup = BeautifulSoup(response.content, "html.parser")
        rows = soup.find_all("tr", class_="clickable-row clickable-row-newtab")
        
        if not rows:
            break

        for row in rows:
            link = row.get("data-href")
            if link:
                report_links.append(link)
        
        page_num += 1

    return report_links

if __name__ == "__main__":
    links = get_report_links()
    print(f"founds {len(links)} malpedia links.")
