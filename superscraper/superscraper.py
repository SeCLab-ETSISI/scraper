import pandas as pd
from utils import extract_pdfs_from_repo, extract_text_from_url, getMinHashFromFullText, is_duplicate, extract_iocs, collection, insert_into_db, load_existing_minhashes_from_db
from urllib.parse import urlparse
from globals import GH_TOKEN
from datasketch import MinHash

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
    existing_minhashes = load_existing_minhashes_from_db()

    ######## i=0
    i = 1
    failed_texts = 0

    for link in links_df['link']:
        link = link.strip()  # clean up any extra whitespace or quotes

        print("------ Processing link: ", i)
        if is_github_url(link):
            owner, repo = link.split('/')[-2:]
            extract_pdfs_from_repo(owner, repo, '../pdf_files', branches=["main", "master"], token=GH_TOKEN)
            print(f"[+] Processing repo {link}")
            # Text from PDFs is processed within extract_pdfs_from_repo function now
        else:
            print(f"Extracting text from URL {link}")
            text = extract_text_from_url(link)
            if text:
                print("Extracting IOCs")
                iocs = extract_iocs(text)
                print("Inserting")
                insert_into_db(text, existing_minhashes, iocs, link)
            else:
                failed_texts += 1
        i += 1
    
    print(f"[!] Failed texts: {failed_texts}")

if __name__ == "__main__":
    main()
