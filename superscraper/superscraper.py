import pandas as pd
from utils import extract_pdfs_from_repo, extract_text_from_url, getMinHashFromFullText, is_duplicate, extract_iocs, insert_into_db, collection
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

def load_existing_minhashes_from_db():
    """
    Load existing MinHashes from MongoDB.

    Returns:
    List of MinHash objects.
    """
    existing_minhashes = []
    for record in collection.find({}, {'minhash': 1}):
        if 'minhash' in record:
            mh = MinHash()
            for digest in record['minhash']:
                mh.update(digest.encode('utf8'))
            existing_minhashes.append(mh)
        else:
            print(f"Record with ID {record['_id']} is missing the 'minhash' field and will be skipped.")
    return existing_minhashes

def main():
    """
    Main function to process links from links.csv and extract data accordingly.
    """
    if GH_TOKEN is None:
        raise ValueError("GitHub token is None.")
    
    links_df = pd.read_csv('../links/links.csv')
    existing_minhashes = load_existing_minhashes_from_db()

    for link in links_df['link']:
        link = link.strip()  # clean up any extra whitespace or quotes
        texts = []

        if is_github_url(link):
            owner, repo = link.split('/')[-2:]
            extract_pdfs_from_repo(owner, repo, '../pdf_files', branches=["main", "master"], token=GH_TOKEN)
            # Text from PDFs is processed within extract_pdfs_from_repo function now
        else:
            text = extract_text_from_url(link)
            if text:
                texts.append(text)

        for text in texts:
            minhash = getMinHashFromFullText(text)
            
            if is_duplicate(minhash, existing_minhashes):
                print("Duplicate found, skipping insertion.")
                continue
            
            iocs = extract_iocs(text)
            insert_into_db(text, minhash, iocs)
            
            existing_minhashes.append(minhash)

if __name__ == "__main__":
    main()
