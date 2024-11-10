from datetime import datetime
import os
import requests
import pandas as pd
import re
from bs4 import BeautifulSoup
import py7zr
from file_analysis_utils import get_all_file_types, compute_hashes
import time
import subprocess
import logging
import pickle
from tqdm import tqdm

logging.basicConfig(filename='vx_underground.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s', filemode='w')

def load_last_scrap_time():
    """Loads the last scraping time from the updater log."""
    with open('./updater.log', 'r') as f:
        lines = f.readlines()
        last_line = lines[-1]
    return datetime.strptime(last_line.strip(), "%Y/%m/%d")

def request_with_retry(url, max_retries=3):
    """
    Sends a GET request to a URL with retries on failure.

    Args:
        url (str): The URL to request.
        max_retries (int): The maximum number of retries.

    Returns:
        requests.Response: The response object.
    """
    for i in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response
        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
        time.sleep(5)
    return None

def download_file(url, local_filename, retries=3):
    """
    Downloads a file from the given URL to the specified local filename, creating directories as needed.

    Args:
        url (str): The URL to download from.
        local_filename (str): The path where the file should be saved.
    """
    os.makedirs(os.path.dirname(local_filename), exist_ok=True)
    url = url.replace("https://vx-underground.org", "https://samples.vx-underground.org")
    for _ in range(retries):
        try:
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                with open(local_filename, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            break
        except requests.exceptions.RequestException as e:
            logging.error(f"Error downloading {url}: {e}")
            time.sleep(5)
            continue

def decompress_file(file_path, password="infected"):
    """
    Extracts a compressed file to its containing directory using the '7z' command.
    Differentiates between files and folders based on filesystem inspection.
    (Note: The method does not use the python library py7zr because it does not support some file encryptions)

    Args:
        file_path (str): The path of the compressed file.

    Returns:
        tuple: A list of extracted files and the count of files extracted.
    """
    # Define the output directory as the same location as the .7z file
    output_dir = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    file_name_no_extension = os.path.splitext(file_name)[0]
    password_list = ["infected", "malware", "virus", "password", "", " ", "virus", "password", f"{file_name_no_extension}", "trojan", "ransomware", "worm", "spyware", "adware", "keylogger", "rootkit", "backdoor", "botnet", "exploit", "phishing", "scareware", "spam", "zombie", "dropper", "logic bomb", "time bomb", "fileless", "polymorphic", "metamorphic", "stealth", "armored", "encrypted", "packed", "obfuscated", "shellcode", "payload", "injection", "heap spray", "buffer overflow", "stack overflow","password", "password123", "123456", "12345678", "qwerty", "abc123", "password1", "1234567", "123123", "123456789"]
    result = None
    for password in password_list:
        try:
            result = subprocess.run(
                ["7z", "x", file_path, f"-o{output_dir}", f"-p{password}", "-y", "-bb3"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                break  # Exit loop if extraction is successful
        except subprocess.CalledProcessError:
            continue
    # Check if extraction was successful
    if result is None or result.returncode != 0:
        logging.error(f"Failed to extract {file_path} with all provided passwords.")
        return None, None

    os.rename(file_path, f"./zips_with_malware/{file_name}")
    # Gather a list of extracted files
    extracted_files = []
    for root, _, files in os.walk(output_dir):
        for file in files:
            extracted_files.append(os.path.join(root, file))
    
    return extracted_files, len(extracted_files)

def extract_all_7z_files(path):
    """
    Extracts all '.7z' files within a directory and moves them to a specified folder.

    Args:
        path (str): The directory to search for '.7z' files.
    """
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".7z") or file.endswith(".zip"):
                decompress_file(os.path.join(root, file))

def get_file_details_vx_underground(file_path):
    """
    Extracts file details from a file path in the vx_underground directory.

    Args:
        file_path (str): The path to the file in the vx_underground directory.

    Returns:
        tuple: A tuple containing the file name, campaign, and year.
    """
    file_name = os.path.splitext(file_path)[0]
    path_parts = file_path.split("vx_underground")[1].split(os.sep)
    year, campaign = path_parts[1], path_parts[2]
    hashes = compute_hashes(file_path)
    return {
        "file_name": file_name,
        "file_path": file_path,
        "sha256": hashes[0],
        "md5": hashes[1],
        "sha1": hashes[2],
        "file_size": os.path.getsize(file_path),
        "campaign": campaign,
        "year": year
    }

def is_compressed_file(file_path):
    """
    Checks if a file is compressed based on its extension.

    Args:
        file_path (str): The path to the file to check.

    Returns:
        bool: True if the file is compressed, False otherwise.
    """
    compressed_extensions = [".zip", ".7z", ".rar", ".tar", ".tar.gz", ".tar.bz2", ".tar.xz", ".tar.zst", ".gzip", ".bzip2", ".xz", ".zstd"]
    return any(ext in file_path.lower() for ext in compressed_extensions)

def is_not_malware(file_path):
    """
    Checks if a file is not malware based on some hand-crafted rules.

    Args:
        file_path (str): The path to the file to check.

    Returns:
        bool: True if the file is not malware, False otherwise.
    """
    not_malware_names = [".yar", ".json", ".txt", "ioc", ".md", "reference", "resources", 
                         "muddyc3-revived", "2016.01.07 - rigging compromise exploit kit_rigging compromise_rigging compromise"]
    return any(name in file_path.lower() for name in not_malware_names)

def filter_file_vx_underground(file_path):
    """
    Filters files based on whether they are malware and whether they are compressed.

    Args:
        file_path (str): The path to the file to filter.

    Returns:
        dict: A dictionary containing file details if the file is malware and not compressed, or None otherwise.
    """
    if is_not_malware(file_path):
        return None
    elif is_compressed_file(file_path):
        extracted_files, n_extracted_files = decompress_file(file_path)
        if extracted_files:
            folder_data = []
            for extracted_file in extracted_files:
                file_details = filter_file_vx_underground(extracted_file)
                if file_details:
                    folder_data.append(file_details)
            return folder_data
        else:
            return None
    else:
        return [get_file_details_vx_underground(file_path)]
    
def generate_csv_vx_underground(folder_path, output_csv):
    """
    Generates a CSV file containing details of all malware files in the vx_underground directory.

    Args:
        folder_path (str): The directory to search for '.7z' files.
        output_csv (str): The output CSV file path.
    """
    file_data = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            if "/Samples/" in file_path:
                if os.path.isfile(file_path):
                    result = filter_file_vx_underground(file_path)
                    if result:
                        file_data.extend(result)
    pd.DataFrame(file_data).to_csv(output_csv, index=False)


def download_vx_underground_archive():
    """
    Downloads the 'vx_underground' archive, extracts all '.7z' files, and generates a CSV of the file information.
    """
    directory = "./vx_underground"
    os.makedirs(directory, exist_ok=True)
    archive_url = "https://vx-underground.org/APTs/Yearly%20Archives"

    logging.info("Starting to download vx_underground files...")
    scrape_base_page_vx(archive_url, download_archive=True) # almost 2h to download all the malware samples
    extract_all_7z_files(directory)
    generate_csv_vx_underground(directory, f"./vx_underground.csv")
    logging.info("Extraction of vx_underground completed.")


def extract_size_modified_date(item):
    """
    Extracts the file size and last modified date from HTML <p> tags.

    Args:
        item (BeautifulSoup Tag): The HTML element containing file information.

    Returns:
        tuple: (file_size, last_modified), both as strings.
    """
    p_tags = item.find_all('p')
    if len(p_tags) < 2:
        return None, None

    size_text = next((p.get_text(strip=True) for p in p_tags if 'Size' in p.text), None)
    modified_text = next((p.get_text(strip=True) for p in p_tags if 'Last modified' in p.text), None)
    
    return (size_text.replace('Size:', '').strip(),
            modified_text.replace('Last modified:', '').strip()) if size_text and modified_text else (None, None)

def scrape_samples_page(samples_url, last_scrap):
    """
    Scrapes file information from a 'Samples' page, comparing the modification date to the last scrape time.

    Args:
        samples_url (str): URL of the 'Samples' page.
        last_scrap (datetime): Timestamp of the last scrape.

    Returns:
        list: Information on files updated since the last scrape.
    """
    file_info_list = []
    response = request_with_retry(samples_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    file_display_div = soup.find('div', id='file-display')

    if file_display_div:
        for item in file_display_div.find_all('div'):
            file_name_tag = item.find('span', class_="truncate")
            if file_name_tag:
                file_name = file_name_tag.text.strip()
                file_size, last_modified = extract_size_modified_date(item)
                if datetime.strptime(last_modified, "%Y/%m/%d") > last_scrap:
                    file_info_list.append({
                        "file_name": file_name,
                        "file_size": file_size,
                        "last_modified": last_modified,
                        "file_link": f"{samples_url}/{file_name}"
                    })
    return file_info_list

def scrape_campaign_page(year_url, last_scrap):
    """
    Scrapes campaign data for a given year, retrieving file information from each campaign's "Samples" page.

    Args:
        year_url (str): The URL for the year page containing campaigns.
        year (str): The year being scraped.
        last_scrap (datetime): The last scraping time to filter updated files.

    Returns:
        dict: A dictionary where keys are campaign names and values are lists of file details.
    """
    campaigns = {}
    response = request_with_retry(year_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for campaign_link in soup.find_all('p'):
        campaign_name = campaign_link.text.strip()
        samples_url = f"{year_url}/{campaign_name}/Samples"
        campaign_files = scrape_samples_page(samples_url, last_scrap)
        if campaign_files:
            campaigns[campaign_name] = campaign_files
        time.sleep(0.1)
    return campaigns

def scrape_base_page_vx(base_url, download_archive=False):
    """
    Iterates over each year on the base URL, scraping or downloading archives.

    Args:
        base_url (str): The base URL to scrape years from.
        download_archive (bool): Whether to download archive files or only scrape information.

    Returns:
        dict: Data for all years and their respective campaigns.
    """
    all_data = {}
    response = request_with_retry(base_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    last_scrap = load_last_scrap_time()
    file_display_div = soup.find('div', id='file-display')
    if file_display_div:
        for year_div in file_display_div.find_all('div'):
            if download_archive:
                year_p = year_div.find('span', class_="truncate")
            else:
                year_p = year_div.find('p')
            if year_p:
                year = year_p.text.strip().split(".")[0]
                if year.isdigit():
                    year_url = f"{base_url}/{year}"
                    logging.info(f"Scraping year: {year}")
                    if download_archive:
                        archive_path = f"./vx_underground/{year}.7z"
                        if not os.path.exists(archive_path):
                            archive_url = f"{base_url}/{year}.7z"
                            download_file(archive_url, archive_path)
                    else:
                        all_data[year] = scrape_campaign_page(year_url, last_scrap)

    return all_data

def handle_new_file_or_folder(file, year, campaign):
    """
    Downloads and decompress a file (could be a folder) and computes its hash, returning relevant information.

    Args:
        file (dict): Dictionary containing file details like name and link.
        year (str): The year associated with the file.
        campaign (str): The campaign associated with the file.

    Returns:
        list: A list of dictionaries containing file details.
    """
    file_name = file['file_name']
    file_link = file['file_link']
    directory = f"./new_vx_underground/{year}/{campaign}/Samples"
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, file_name)

    download_file(file_link, file_path)
    extracted_files, n_extracted_files = decompress_file(file_path)
    if not extracted_files:
        return None
    if n_extracted_files > 2:
        logging.warning(f"Folder extracted with nfiles: {n_extracted_files} files. Path:\n{file_path}")
    
    new_details_to_add = []
    for extracted_file in extracted_files:
        file_details = get_file_details_vx_underground(extracted_file)
        new_details_to_add.append(file_details)
    
    return new_details_to_add

def move_new_file_vx_folder(file_path):
    """
    Moves a file to the appropriate folder based on its hash.

    Args:
        file_path (str): The path to the file to move.
    
    Returns:
        str: The new path of the file.
    """
    path_parts = file_path.split("vx_underground")[1].split(os.sep)
    year, campaign, file_name = path_parts[1], path_parts[2], path_parts[-1]
    new_path = f"./vx_underground/{year}/{campaign}/Samples/{file_name}"
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    os.rename(file_path, new_path)
    return new_path

def insert_new_file_in_malware_df(file_details):
    """
    Gathers information about a new file and inserts it into the malware DataFrame.

    Args:
        file_details (dict): The details of the new file.
    
    Returns:
        pd.Series: The new row to insert into the malware DataFrame.
    """
    file_types = get_all_file_types(file_details['file_path'], file_details['sha256'])
    file_details.update({
        'source': 'vx_underground',
        'file_paths': [file_details['file_path']],
        'available': True,
        'file_type_magika': file_types[0],
        'file_type_libmagic': file_types[1],
        'file_type_exiftool': file_types[2],
        'virustotal_reports': None
    })
    return file_details

def add_extra_information_malware_df(file_details, malware_df):
    """
    Adds extra information to an existing file in the malware DataFrame.

    Args:
        file_details (dict): The details of the file to update.
        malware_df (pd.DataFrame): The DataFrame containing malware information.
    """
    # update the "file_paths" column in malware_df
    idx = malware_df[malware_df['sha256'] == file_details['sha256']].index[0]
    current_file_paths = malware_df.at[idx, 'file_paths'] or ""
    file_paths = set(current_file_paths.split(", "))
    file_paths.add(file_details['file_path'])
    malware_df.at[idx, 'file_paths'] = ", ".join(sorted(file_paths))

    current_sources = malware_df.at[idx, 'source'] or ""
    sources = set(current_sources.split(", "))
    sources.add("vx_underground")
    malware_df.at[idx, 'source'] = ", ".join(sorted(sources))

    # Update the 'available' column in malware_df
    malware_df.at[idx, 'available'] = True
    new_row = malware_df.loc[idx].copy()
    return idx, new_row
def insert_new_file_in_malware_df(file_details):
    """
    Prepares a new row for the malware DataFrame by adding relevant fields.

    Args:
        file_details (dict): The details of the new file to insert.

    Returns:
        dict: The updated file details with additional fields for the DataFrame.
    """
    file_types = get_all_file_types(file_details['file_path'], file_details['sha256'])
    file_details.update({
        'source': 'vx_underground',
        'file_paths': [file_details['file_path']],
        'available': True,
        'file_type_magika': file_types[0],
        'file_type_libmagic': file_types[1],
        'file_type_exiftool': file_types[2],
        'virustotal_reports': None
    })
    return file_details

def add_extra_information_malware_df(file_details, updated_row):
    """
    Updates information for an existing file row without modifying the original DataFrame.

    Args:
        file_details (dict): The details of the file to update.
        existing_row (pd.Series): The existing row from malware_df to be updated.

    Returns:
        pd.Series: The updated row with additional information.
    """
    # Update the "file_paths" field
    current_file_paths = updated_row.get('file_paths', "")
    file_paths = set(current_file_paths.split(", ")) if current_file_paths else set()
    file_paths.add(file_details['file_path'])
    updated_row['file_paths'] = ", ".join(sorted(file_paths))

    # Update the 'source' field
    current_sources = updated_row.get('source', "")
    sources = set(current_sources.split(", ")) if current_sources else set()
    sources.add("vx_underground")
    updated_row['source'] = ", ".join(sorted(sources))

    # Update the 'available' field
    updated_row['available'] = True

    return updated_row

def update_vx_underground(base_url="https://vx-underground.org/APTs"):
    """
    Updates the vx_underground dataset by scraping new files and adding them to the existing dataset.

    Args:
        base_url (str): The base URL to scrape for new files.

    The updated dataset is saved to a new CSV file.
    """
    vx_underground = pd.read_csv('./vx_underground.csv')
    malware_df = pd.read_pickle('./malware_df.pkl')
    new_malware_rows = []
    new_vx_rows = []
    
    unseen_data = scrape_base_page_vx(base_url)

    total_files = sum(len(files) for campaigns in unseen_data.values() for files in campaigns.values())
    with tqdm(total=total_files, desc="Processing files", file=open("./tdqm_unseen.log", "w")) as pbar:
        for year, campaigns in unseen_data.items():
            for campaign, files in campaigns.items():
                pbar.set_postfix(year=year, campaign=campaign)
                for file in files:
                    if os.path.splitext(file['file_name'])[0] not in vx_underground['file_name'].values: # double check for avoiding duplicates
                        new_file_or_folder = handle_new_file_or_folder(file, year, campaign) # it can decompress a folder or a file, anyway it returns a list
                        if new_file_or_folder:
                            for file_details in new_file_or_folder:
                                if file_details['sha256'] not in vx_underground['sha256'].values: # double check (modify date and sha256) for avoiding duplicates
                                    file_details['file_path'] = move_new_file_vx_folder(file_details['file_path'])
                                    new_vx_rows.append(file_details)
                                    if file_details['sha256'] not in malware_df['sha256'].values: # if the file is not already in malware_df by other source
                                        # Insert a new row for malware_df
                                        new_row = insert_new_file_in_malware_df(file_details)
                                        new_malware_rows.append(new_row)
                                    else: # if the file is already in malware_df by other source
                                        idx = malware_df[malware_df['sha256'] == file_details['sha256']].index[0]
                                        updated_row = add_extra_information_malware_df(file_details, malware_df.loc[idx].copy())
                                        malware_df.loc[idx] = updated_row
                        pbar.update(1)

    if new_malware_rows:
        malware_df = pd.concat([malware_df, pd.DataFrame(new_malware_rows)], ignore_index=True)
        logging.info(f"Added {len(new_malware_rows)} new rows to malware_df.")
    if new_vx_rows:
        vx_underground = pd.concat([vx_underground, pd.DataFrame(new_vx_rows)], ignore_index=True)
        vx_underground.to_csv('./vx_underground_after_update.csv', index=False)
        malware_df.to_pickle('./malware_df_after_update.pkl')
        logging.info(f"Added {len(new_vx_rows)} new rows to vx_underground.")
    
    with open('./updater.log', 'a') as f:
        f.write(f"{datetime.now().strftime('%Y/%m/%d')}\n")

    logging.info(f"Updated vx_underground shape: {vx_underground.shape}")
    logging.info(f"Updated malware_df shape: {malware_df.shape}")

def main():
    logging.info("Starting to download vx_underground files...")
    logging.info(datetime.now())
    download_vx_underground_archive()
    update_vx_underground()
    logging.info("Extraction of vx_underground completed.")
    logging.info(datetime.now())


#if __name__ == "__main__":
#    main()