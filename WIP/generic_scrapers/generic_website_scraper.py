import requests
from readability import Document
from bs4 import BeautifulSoup

page_num=1
url="https://blogs.blackberry.com/bin/blogs?page={page_num}&category=https://blogs.blackberry.com/en/category/research-and-intelligence&locale=en"

response = requests.get(url)
doc = Document(response.content)
str = doc.summary()

soup = BeautifulSoup(str, 'html.parser')
clean = soup.text.strip()

titulo  = doc.title()
print(titulo)
print(clean) 
