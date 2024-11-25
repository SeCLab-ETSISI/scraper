import pandas as pd
import asyncio
import requests
import zipfile
import io
from urllib.parse import urlparse
from datasketch import MinHash
import os
import json
from pymongo import MongoClient
import datetime


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
    # download_vx_underground_archive,
    # update_vx_underground
)
from urllib.parse import urlparse
from globals import GH_TOKEN, SCRAPING_TIME, 
from datasketch import MinHash
from datetime import datetime

from utils.vx_underground_utils import (
    download_vx_underground_archive, 
    update_vx_underground
)

from utils.dataframe_utils import (
    load_all_datasets,
    handle_duplicates,
    add_filetype,
    generate_venn_diagram,
    insert_dict_to_mongo
)


from globals import SCRAPING_TIME, GH_TOKEN, MONGO_CONNECTION_STRING, MONGO_DATABASE, MONGO_MALWARE_COLLECTION, VIRUSTOTAL_API_KEY, PATH_VT_REPORTS, MONGO_VIRUSTOTAL_COLLECTION

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
    malware_df = load_all_datasets(base_path="./")
    malware_df = handle_duplicates(malware_df)
    print(f"Final DataFrame contains {len(malware_df)} unique samples but there are {malware_df['file_path'].isnull().sum()} missing files")
    print("Of those missing, they come from:\n",malware_df[malware_df["available"]==False]["source"].value_counts())
    print("="*40)
    if plot_venn:
        generate_venn_diagram(malware_df)

    malware_df = add_filetype(malware_df)
    malware_df["date_added"] = SCRAPING_TIME

    malware_df.to_pickle("malware_df.pkl")

    client = MongoClient(MONGO_CONNECTION_STRING)
    try:
        db = client[MONGO_DATABASE]
        collection = db[MONGO_MALWARE_COLLECTION]
        for idx, row in malware_df.iterrows():
            try:
                insert_dict_to_mongo(row.to_dict(), collection)
            except Exception as e:
                print(f"Failed to insert row at main when processing malware. Row at index {idx}. Exception {e}")
    finally:
        client.close()


    print('------ Malware processing completed ------')

def get_virustotal_report(sha256):
    """
    Get the VirusTotal report for a given file hash (SHA-256).

    :param api_key: VirusTotal API key.
    :param sha256: SHA-256 hash of the file.
    :return: JSON response from VirusTotal API.
    """
    url = f"https://www.virustotal.com/api/v3/files/{sha256}"
    headers = {
        "x-apikey": VIRUSTOTAL_API_KEY
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # Save the report to a JSON file
        with open(f"{PATH_VT_REPORTS}/{sha256}.json", 'w') as file:
            json.dump(response.json(), file)
        return True
    else:
        print(f"Failed to get report for {sha256}. Status code: {response.status_code}")
        return None

def insert_vt_report_to_mongo(report_path, collection):
    """
    Insert the VirusTotal reports to the MongoDB collection.

    Args:
        report_path (str): Path to the VirusTotal report.
        collection (pymongo.collection.Collection): Collection to insert the reports.
    
    """
    with open(report_path, 'r') as file:
        report = json.load(file)
    collection.insert_one(report)

def update_virustotal_reports(malware_df):
    """
    Update the VirusTotal reports by downloading the latest version of the reports.
    """
    client = MongoClient(MONGO_CONNECTION_STRING)
    try:
        db = client[MONGO_DATABASE]
        collection = db[MONGO_VIRUSTOTAL_COLLECTION]
        for idx, row in malware_df.iterrows():
            if not row["virustotal_report_path"]:
                vt_report = get_virustotal_report(row["sha256"])
                if vt_report:
                    row["virustotal_report_path"] = f"{PATH_VT_REPORTS}/{row['sha256']}.json"
                    insert_vt_report_to_mongo(row["virustotal_report_path"], collection)
    finally:
        client.close()


def update_malware():
    """
    Update the malware datasets by downloading their last version (at the current version only VX Underground). 
    """
    print("------ Updating malware ------")
    client = MongoClient(MONGO_CONNECTION_STRING)
    try:
        db = client[MONGO_DATABASE]
        collection = db[MONGO_MALWARE_COLLECTION]
        malware_df = update_vx_underground(collection)
    finally:
        client.close()

    update_virustotal_reports(malware_df)

def insert_virustotal_reports():
    """
    Upload all the JSON files contained under their path to a new MongoDB collection.
    
    """
    client = MongoClient(MONGO_CONNECTION_STRING)
    try:
        db = client[MONGO_DATABASE]
        collection = db[MONGO_VIRUSTOTAL_COLLECTION]
        for filename in os.listdir(PATH_VT_REPORTS):
            if filename.endswith(".json"):
                insert_vt_report_to_mongo(f"{PATH_VT_REPORTS}/{filename}", collection)
    finally:
        client.close()
        print("------ Upload completed ------")

def download_synonyms():
    """

    """
    pass

def process_synonyms():
    """
    
    """
    pass

def update_synonyms():
    """
    
    """
    pass
def main():
    if not os.path.exists("./malware_df.pkl"): # check if the base content is already downloaded
        download_malware()
        process_malware()
        insert_virustotal_reports()

    update_malware() # always update malware

    if not os.path.exists("./synonyms.pkl"):
        download_synonyms()
        process_synonyms()
    else:
        update_synonyms()

        
if __name__ == "__main__":
    main()
