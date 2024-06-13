import requests
from bs4 import BeautifulSoup
from typing import List

def extract_paragraphs(url: str) -> List[str]:
    """
    Extract the text of all <p> tags from a given URL.

    Parameters:
    url (str): The URL of the webpage to extract paragraphs from.

    Returns:
    List[str]: A list of strings, each containing the text of a <p> tag.
    """
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"[-] Failed to load page with status code {response.status_code}")
    
    soup = BeautifulSoup(response.content, 'lxml')
    
    paragraphs = soup.find_all('p')
    texts = [p.get_text() for p in paragraphs]
    
    return texts

if __name__ == "__main__":
    url = "https://www.loquesea.com"
    try:
        paragraphs_text = extract_paragraphs(url)
        for i, paragraph in enumerate(paragraphs_text):
            print(f"Paragraph {i+1}: {paragraph}\n")
    except Exception as e:
        print(str(e))

