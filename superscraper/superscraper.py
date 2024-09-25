import pandas as pd
import asyncio
from utils import (
    extract_pdfs_from_repo,
    extract_text_from_url,
    getMinHashFromFullText,
    is_duplicate,
    extract_iocs,
    collection,
    insert_into_db,
    load_existing_minhashes_from_db,
    get_orkl_report,
    process_orkl_report
)
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

async def main():
    """
    Main function to process links from links.csv and extract data accordingly.
    """
    if GH_TOKEN is None:
        raise ValueError("GitHub token is None.")
    
    links_df = pd.read_csv('../links/links.csv')
    existing_minhashes = load_existing_minhashes_from_db()

    i = 1
    failed_texts = 0
    successful_texts = 0

    for link in links_df['link']:
        link = link.strip()

        print("------ Processing link: ", i)
        if is_github_url(link):
            owner, repo = link.split('/')[-2:]
            await extract_pdfs_from_repo(owner, repo, '../pdf_files', branches=["main", "master"], token=GH_TOKEN)
            print(f"[+] Processing repo {link}")
        else:
            print(f"Extracting text from URL {link}")
            text = await extract_text_from_url(link)
            if text:
                print("Extracting IOCs")
                iocs = extract_iocs(text)
                print("Inserting")
                insert_into_db(text, existing_minhashes, iocs, link)
                successful_texts += 1
            else:
                failed_texts += 1
        i += 1

    print("------ Processing ORKL reports ------")
    offset = 0
    while True:
        reports = await get_orkl_report(offset=offset, limit=1)
        if reports is None:
            print(f"No more reports found at offset {offset}. Stopping.")
            break
        
        for report in reports:
            await process_orkl_report(report, existing_minhashes)

        offset += 1

    print(f"[!] Failed inserts: {failed_texts}")
    print(f"[!] Successful inserts: {successful_texts}")

if __name__ == "__main__":
    asyncio.run(main())
