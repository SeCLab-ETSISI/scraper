import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

###################
# This one contains the commented section links and adds more.
###################
url = "https://cloudblog.withgoogle.com/topics/threat-intelligence/rss/"

response = requests.get(url)

if response.status_code != 200:
    print("Error:", response.status_code)
    exit()
root = ET.fromstring(response.text)
links = []

# Iterate over all the <item> tags in the XML
for item in root.iter("item"):
    # Extract the link from the <link> tag
    link = item.find("link").text
    links.append(link)
urls = list(set(links))


# # Make a GET request to the page
# url = "https://cloud.google.com/blog/topics/threat-intelligence"
# response = requests.get(url)

# # Parse the HTML using BeautifulSoup
# soup = BeautifulSoup(response.text, "html.parser")

# links = []
# for a in soup.find_all("a", href=True):
#     link = a["href"]
#     if "https://cloud.google.com/blog/topics/threat-intelligence/" in link:
#         links.append(link)

# urls = list(set(links)) # Around 10