import requests
from readability import Document
from bs4 import BeautifulSoup

url = "https://www.sentinelone.com/labs/a-glimpse-into-future-scarcruft-campaigns-attackers-gather-strategic-intelligence-and-target-cybersecurity-professionals/"

response = requests.get(url)
doc = Document(response.content)
str = doc.summary()

soup = BeautifulSoup(str, 'html.parser')
clean = soup.text.strip()

titulo  = doc.title()
print(titulo)
print(clean) 
