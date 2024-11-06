from datetime import datetime
import os
import requests
import hashlib
import pandas as pd
import re
from bs4 import BeautifulSoup
import py7zr
from file_analysis_utils import get_all_file_types, compute_hashes

def download_file(url, local_filename):
    """
    Downloads a file from the given URL to the specified local filename, creating directories as needed.

    Args:
        url (str): The URL to download from.
        local_filename (str): The path where the file should be saved.
    """
    os.makedirs(os.path.dirname(local_filename), exist_ok=True)
    url = url.replace("https://vx-underground.org", "https://samples.vx-underground.org")
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def extract_7z_file(file_path):
    """
    Extracts a '.7z' file to its containing directory.

    Args:
        file_path (str): The path of the '.7z' file.
    """
    with py7zr.SevenZipFile(file_path, mode='r', password='infected') as archive:
        archive.extractall(path=os.path.dirname(file_path))


def extract_all_7z_files(path):
    """
    Extracts all '.7z' files within a directory and moves them to a specified folder.

    Args:
        path (str): The directory to search for '.7z' files.
    """
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".7z"):
                file_path = os.path.join(root, file)
                extract_7z_file(file_path)
                os.rename(file_path, f"./zips_with_malware/{file}")

def find_7z_files_and_generate_csv(folder_path, output_csv):
    """
    Finds '.7z' files in a given folder, computes their hashes, and saves the data to a CSV file.

    Args:
        folder_path (str): The directory to search for '.7z' files.
        output_csv (str): The output CSV file path.
    """
    file_data = []

    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith('.7z') and "/Samples/" in file_path:
                file_name = os.path.splitext(file)[0]
                file_path_no_ext = os.path.splitext(file_path)[0]
                path_parts = file_path_no_ext.split("vx_underground")[1].split(os.sep)
                year, campaign = path_parts[1], path_parts[2]

                if os.path.isfile(file_path_no_ext):
                    hashes = compute_hashes(file_path_no_ext)
                    file_data.append({
                        "file_name": file_name,
                        "file_path": file_path_no_ext,
                        "sha256": hashes[0],
                        "md5": hashes[1],
                        "sha1": hashes[2],
                        "file_size": os.path.getsize(file_path_no_ext),
                        "campaign": campaign,
                        "year": year
                    })

                elif os.path.isdir(file_path_no_ext):
                    print(f"Processing the folder: {file_path_no_ext}")
                    for inner_file in os.listdir(file_path_no_ext):
                        if re.match(r'^[a-fA-F0-9]{64}$', inner_file):
                            print(f"\tThe file is a hash and will be stored as a sample: {inner_file}")
                            file_path_inner = os.path.join(file_path_no_ext, inner_file)
                            hashes = compute_hashes(file_path_inner)
                            file_data.append({
                                "file_name": inner_file,
                                "file_path": file_path_inner,
                                "sha256": hashes[0],
                                "md5": hashes[1],
                                "sha1": hashes[2],
                                "file_size": os.path.getsize(file_path_inner),
                                "campaign": campaign,
                                "year": year
                            })

    pd.DataFrame(file_data).to_csv(output_csv, index=False)


def download_vx_underground_archive():
    """
    Downloads the 'vx_underground' archive, extracts all '.7z' files, and generates a CSV of the file information.
    """
    print("Starting to download vx_underground files...")
    directory = "./vx_underground"
    os.makedirs(directory, exist_ok=True)
    base_url = "https://vx-underground.org/APTs"
    scrape_all_years(base_url, download_archive=True)
    extract_all_7z_files(directory)
    find_7z_files_and_generate_csv(directory, f"./vx_underground.csv")
    print("Extraction of vx_underground completed.")

def load_last_scrap_time():
    """Loads the last scraping time from the updater log."""
    with open('./updater.log', 'r') as f:
        lines = f.readlines()
        last_line = lines[-1]
    return datetime.strptime(last_line.strip(), "%Y/%m/%d")

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


def scrape_file_info(samples_url, last_scrap):
    """
    Scrapes file information from a 'Samples' page, comparing the modification date to the last scrape time.

    Args:
        samples_url (str): URL of the 'Samples' page.
        last_scrap (datetime): Timestamp of the last scrape.

    Returns:
        list: Information on files updated since the last scrape.
    """
    file_info_list = []
    response = requests.get(samples_url)
    if response.status_code != 200:
        print(f"No samples from {samples_url}")
        return []

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

def scrape_campaign_samples(year_url, year, last_scrap):
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
    response = requests.get(year_url)
    if response.status_code != 200:
        print(f"No campaigns from {year_url}")
        return campaigns

    soup = BeautifulSoup(response.text, 'html.parser')
    for campaign_link in soup.find_all('p'):
        campaign_name = campaign_link.text.strip()
        samples_url = f"{year_url}/{campaign_name}/Samples"
        campaign_files = scrape_file_info(samples_url, last_scrap)
        if campaign_files:
            campaigns[campaign_name] = campaign_files

    return campaigns


def scrape_all_years(base_url, download_archive=False):
    """
    Iterates over each year on the base URL, scraping or downloading archives.

    Args:
        base_url (str): The base URL to scrape years from.
        download_archive (bool): Whether to download archive files or only scrape information.

    Returns:
        dict: Data for all years and their respective campaigns.
    """
    all_data = {}
    response = requests.get(base_url)
    if response.status_code != 200:
        print(f"No years from {base_url}")
        return all_data

    soup = BeautifulSoup(response.text, 'html.parser')
    last_scrap = load_last_scrap_time()
    file_display_div = soup.find('div', id='file-display')

    if file_display_div:
        for year_div in file_display_div.find_all('div'):
            year_p = year_div.find('p')
            if year_p:
                year = year_p.text.strip()
                if year.isdigit():
                    year_url = f"{base_url}/{year}"
                    print(f"Scraping year: {year}")
                    if download_archive:
                        archive_path = f"./vx_underground/{year}.7z"
                        if not os.path.exists(archive_path):
                            archive_url = f"https://samples.vx-underground.org/APTs/Yearly%20Archives/{year}.7z"
                            download_file(archive_url, archive_path)
                    else:
                        all_data[year] = scrape_campaign_samples(year_url, year, last_scrap)

    return all_data


def handle_file(file, year, campaign):
    """
    Downloads a file and computes its hash, returning relevant information.

    Args:
        file (dict): Dictionary containing file details like name and link.
        year (str): The year associated with the file.
        campaign (str): The campaign associated with the file.

    Returns:
        dict: A dictionary containing file details and hashes.
    """
    file_name = file['file_name']
    file_link = file['file_link']
    directory = f"./vx_underground/{year}/{campaign}/Samples"
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, file_name)

    download_file(file_link, file_path)
    file_path_no_ext = os.path.splitext(file_path)[0]
    hashes = compute_hashes(file_path_no_ext)

    return {
        "file_name": file_name,
        "file_path": file_path_no_ext,
        "sha256": hashes[0],
        "md5": hashes[1],
        "sha1": hashes[2],
        "file_size": os.path.getsize(file_path_no_ext),
        "campaign": campaign,
        "year": year
    }


def update_vx_underground():
    """
    Updates the vx_underground archive by scraping new files, downloading them, and appending details to existing data files.
    """
    base_url = "https://vx-underground.org/APTs"
    vx_underground = pd.read_csv('./vx_underground.csv')
    malware_df = pd.read_pickle('./malware_df.pkl')

    print("Original vx_underground shape:", vx_underground.shape)
    print("Original malware_df shape:", malware_df.shape)

    all_data = scrape_all_years(base_url)
    malware_df_modified = False

    for year, campaigns in all_data.items():
        for campaign, files in campaigns.items():
            for file in files:
                file_details = handle_file(file, year, campaign)
                vx_underground = vx_underground.append(file_details, ignore_index=True)

                if file_details['sha256'] not in malware_df['sha256'].values:
                    malware_df_modified = True
                    file_details.update({
                        'source': 'vx_underground',
                        'file_paths': [file_details['file_path']],
                        'available': True
                    })
                    file_types = get_all_file_types(file_details['file_path'], file_details['sha256'])
                    file_details.update({
                        'file_type_magika': file_types[0],
                        'file_type_libmagic': file_types[1],
                        'file_type_exiftool': file_types[2],
                        'virustotal_reports': None
                    })
                    malware_df = malware_df.append(file_details, ignore_index=True)

    print("Updated vx_underground shape:", vx_underground.shape)
    print("Updated malware_df shape:", malware_df.shape)

    vx_underground.to_csv('./vx_underground.csv', index=False)
    if malware_df_modified:
        malware_df.to_pickle('./malware_df.pkl')

    with open('./updater.log', 'a') as f:
        f.write(f"{datetime.now().strftime('%Y/%m/%d')}\n")
    #vx_underground.to_csv('./vx_underground.csv', index=False)

    #if malware_df_modified:
    #    malware_df.to_pickle('./malware_df.pkl')

    #vx_underground.drop_duplicates(subset=['sha256'], inplace=True)
"""
print(f"Scraping started at {datetime.now()}")
all_data = scrape_all_years(BASE_URL)
with open('all_data.pkl', 'wb') as f:
    pickle.dump(all_data, f)
print(f"Scraping completed at {datetime.now()}")
"""
if __name__ == "__main__":
    download_vx_underground_archive()
    update_vx_underground()