import pandas as pd
from utils import extract_pdfs_from_repo, extract_text_from_url
from urllib.parse import urlparse
from globals import GH_TOKEN

def is_github_url(url):
    """
    Check if the given URL is a GitHub URL.

    :param url: URL to check.
    :return: True if URL is a GitHub URL, False otherwise.
    """
    return 'github.com' in urlparse(url).netloc

def main():
    """
    Main function to process links from links.csv and extract data accordingly.
    """
    if GH_TOKEN is None:
        raise ValueError("GitHub token is None.")
    
    links_df = pd.read_csv('../links/links.csv')
    for link in links_df['link']:
        link = link.strip()  # clean up any extra whitespace or quotes
        if is_github_url(link):
            owner, repo = link.split('/')[-2:]
            extract_pdfs_from_repo(owner, repo, '../pdf_files', branches=["main", "master"], token=GH_TOKEN)
        else:
            extract_text_from_url(link)

if __name__ == "__main__":
    main()
