import pandas as pd
import asyncio
import requests
import zipfile
import io
from utils.utils import (
    extract_pdfs_from_repo,
    extract_text_from_url,
    getMinHashFromFullText,
    is_duplicate,
    extract_iocs,
    collection,
    insert_into_db,
    load_existing_minhashes_from_db,
    get_orkl_report,
    process_orkl_report,
    download_vx_underground_archive,
    update_vx_underground
)
from urllib.parse import urlparse
from globals import GH_TOKEN
from datasketch import MinHash
import os

from utils.dataframe_utils import (
    load_all_datasets,
    handle_duplicates,
    add_filetype,
    generate_venn_diagram
)

def is_github_url(url):
    """
    Check if the given URL is a GitHub URL.

    :param url: URL to check.
    :return: True if URL is a GitHub URL, False otherwise.
    """
    return 'github.com' in urlparse(url).netloc

def download_github_repo_as_zip(owner, repo, branch="main"):
    """
    Download a GitHub repository as a zip file.
    """
    url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
    response = requests.get(url)
    
    if response.status_code == 200:
        # Download and extract the zip file
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            zip_ref.extractall(f"{repo}-{branch}")
        print(f"{repo} repository downloaded and extracted to '{repo}-{branch}' folder.")
    else:
        print("Failed to download repository. Please check the repository name and branch.")
    

async def process_reports():
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
        reports = get_orkl_report(offset=offset, limit=1)
        if reports is None:
            print(f"No more reports found at offset {offset}. Stopping.")
            break
        
        for report in reports:
            process_orkl_report(report, existing_minhashes)

        offset += 1

    print(f"[!] Failed inserts: {failed_texts}")
    print(f"[!] Successful inserts: {successful_texts}")

def download_malware():
    """
    Download the malware datasets from GitHub and VX Underground. The rest of datasets are manuallt downloaded because they are not openly available.
    """
    print("------ Downloading malware ------")
    download_github_repo_as_zip("cyber-research", "APTMalware")
    download_vx_underground_archive() # Download VX Underground archive and creates a CSV file with the malware information.
    print("------ Download completed ------")

def process_malware(plot_venn=True):
    """
    Merge all the datasets of malware, filter duplicates and process the binaries to obtain the file type.
    """
    print("------ Processing malware ------")
    df_malware = load_all_datasets(base_path="./")
    df_malware = handle_duplicates(df_malware)
    print(f"Final DataFrame contains {len(df_malware)} unique samples but there are {df_malware['file_path'].isnull().sum()} missing files")
    print("Of those missing, they come from:\n",df_malware[df_malware["available"]==False]["source"].value_counts())
    print("="*40)
    if plot_venn:
        generate_venn_diagram(df_malware)

    df_malware = add_filetype(df_malware)
    df_malware.to_pickle("malware_df.pkl")
    print('------ Malware processing completed ------')

def update_malware():
    """
    Update the malware datasets by downloading the last version of VX Underground.
    """
    print("------ Updating malware ------")
    update_vx_underground()
    print("------ Update completed ------")

def download_synonyms():
    print("------ Downloading synonyms ------")
    download_github_repo_as_zip("cyber-research", "synonyms")
    print("------ Download completed ------")

def process_synonyms():
    pass
    
def main():
    # process the reports
    asyncio.run(process_reports())

    if not os.path.exists("./malware_df.pkl"): # check if the base content is already downloaded
        download_malware()
        process_malware()
    else:
        update_malware()

    if not os.path.exists("./synonyms.pkl"):
        download_synonyms()
        process_synonyms()
    else:
        update_synonyms()

if __name__ == "__main__":
    main()