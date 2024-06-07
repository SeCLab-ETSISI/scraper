import requests
from bs4 import BeautifulSoup

# URL of the page to scrape
url = "https://unit42.paloaltonetworks.com/tag/apt/"

# Send a GET request to the page
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the page content
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find all the report links
    report_links = []
    for article in soup.find_all("article"):
        link_tag = article.find("a")
        if link_tag and 'href' in link_tag.attrs:
            report_links.append(link_tag['href'])
else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")

# Make a GET request to the AJAX URL
url = "https://unit42.paloaltonetworks.com/wp-admin/admin-ajax.php?action=news_infinite&data%5Btag%5D=1703&data%5Boffset%5D=15"
headers = {
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}
response = requests.get(url, headers=headers)

# Parse the HTML using BeautifulSoup
soup = BeautifulSoup(response.text, "html.parser")

links = []
# Extract the links
for a in soup.find_all("a", href=True):
    link = a["href"].replace("\\","").replace('"', '')
    if not "/author/" in link:
        links.append(link)
links = list(set(links))

urls = list(set(report_links + links)) # Around 15