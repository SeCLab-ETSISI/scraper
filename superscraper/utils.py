import os, re
import requests
from typing import List
from pymongo import MongoClient
from readability.readability import Document
from bs4 import BeautifulSoup
import pdfplumber
from datasketch import MinHash
import aiohttp

from globals import HEADERS, MONGO_CONNECTION_STRING, MONGO_DATABASE, MONGO_COLLECTION, GH_TOKEN, ORKL_API_URL, SCRAPING_TIME


client = MongoClient(MONGO_CONNECTION_STRING)
db = client[MONGO_DATABASE]
collection = db[MONGO_COLLECTION]

def get_github_repo_commit_sha(owner: str, repo: str, branches: List[str], token: str) -> str:
    """
    Get the SHA of the latest commit on the specified branches of a GitHub repository.

    :param owner: Owner of the repository.
    :param repo: Name of the repository.
    :param branches: List of branches to fetch the commit SHA from.
    :param token: GitHub personal access token for authentication.
    :return: SHA of the latest commit and the valid branch name.
    """
    if token is None:
        raise ValueError("[!] GitHub token is None.")
    headers = {'Authorization': f'token {token}'}
    print(f"Using token in get_github_repo_commit_sha: {token[:4]}...")  # Debugging statement
    for branch in branches:
        url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}"
        print(f"Fetching branch info from URL: {url}")  # Debugging statement
        response = requests.get(url, headers=headers, timeout=10)# , verify=False)
        if response.status_code == 200:
            return response.json()['commit']['sha'], branch
        elif response.status_code in [401, 403, 404]:
            print(f"[-] Branch {branch} not found or access denied: {response.status_code}")
        else:
            print(f"[-] Error fetching commit SHA for branch {branch}: {response.status_code} - {response.text}")
            response.raise_for_status()
    
    raise ValueError("[?] None of the specified branches were found in the repository.")


async def get_github_repo_commit_sha(owner: str, repo: str, branches: List[str], token: str) -> tuple:
    if token is None:
        raise ValueError("[!] GitHub token is None.")
    
    headers = {'Authorization': f'token {token}'}
    
    async with aiohttp.ClientSession() as session:
        for branch in branches:
            url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}"
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return (await response.json())['commit']['sha'], branch
                elif response.status in [401, 403, 404]:
                    print(f"[-] Branch {branch} not found or access denied: {response.status}")
                else:
                    print(f"[-] Error fetching commit SHA for branch {branch}: {response.status} - {await response.text()}")
    
    # default value if no branches were found
    return None, None



def get_github_repo_tree(owner: str, repo: str, sha: str, token: str) -> List[dict]:
    """
    Get the entire tree of a GitHub repository.

    :param owner: Owner of the repository.
    :param repo: Name of the repository.
    :param sha: SHA of the commit to fetch the tree from.
    :param token: GitHub personal access token for authentication.
    :return: List of all files and directories in the repository.
    """
    if token is None:
        raise ValueError("[!] GitHub token is None.")
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{sha}?recursive=1"
    headers = {'Authorization': f'token {token}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('tree', [])
    else:
        print(f"[-] Error fetching repository tree: {response.status_code} - {response.text}")
        response.raise_for_status()

def download_file(url: str, local_path: str, token: str = None) -> None:
    """
    Download a file from a URL to a local path.

    :param url: URL of the file to download.
    :param local_path: Local path to save the downloaded file.
    :param token: GitHub personal access token for authentication.
    """
    headers = {'Authorization': f'token {token}'} if token else {}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with open(local_path, 'wb') as file:
            file.write(response.content)
    else:
        print(f"[-] Error downloading file: {response.status_code} - {response.text}")
        response.raise_for_status()

async def extract_pdfs_from_repo(owner: str, repo: str, local_dir: str, branches: List[str], token: str = None) -> None:
    """
    Extract all PDF files from a GitHub repository and save them locally.

    :param owner: Owner of the repository.
    :param repo: Name of the repository.
    :param local_dir: Local directory to save the PDF files.
    :param branches: List of branches to check for PDF files.
    :param token: GitHub personal access token for authentication.
    """
    if token is None:
        raise ValueError("[!] GitHub token is None.")
    print(f"Using token in extract_pdfs_from_repo: {token[:4]}...")  # Debugging statement
    repo_dir = os.path.join(local_dir, repo)
    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)

    sha = None
    valid_branch = None
    for branch in branches:
        try:
            sha, valid_branch = await get_github_repo_commit_sha(owner, repo, [branch], token)
            if sha:  # Check if sha is valid
                break  # Stop if a valid branch is found
        except ValueError as e:
            print(f"[-] Error finding branch '{branch}': {e}")
    
    if not sha:
        print(f"[-] No valid branches found in {repo}.")
        return

    tree = get_github_repo_tree(owner, repo, sha, token)
    
    if not tree:
        print(f"[-] No files found in the repository tree for branch '{valid_branch}'.")
        return

    found_pdfs = False

    for item in tree:
        if item['type'] == 'blob' and item['path'].endswith('.pdf'):
            found_pdfs = True
            file_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{valid_branch}/{item['path']}"
            
            try:
                print(f"\t ╰─[📜] Downloading {item['path']} from {file_url}")
                local_path = os.path.join(repo_dir, os.path.basename(item['path']))
                download_file(file_url, local_path, token)
                text = get_text_from_pdf(local_path)
                if text:
                    minhash = getMinHashFromFullText(text)
                    iocs = extract_iocs(text)
                    insert_into_db(text, minhash, iocs, repo)
            except Exception as e:
                print(f"[-] Error processing {file_url}: {e}")
    
    if not found_pdfs:
        print(f"[-] No PDF files found in the repository {repo} on branch '{valid_branch}'.")


def get_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file.

    :param pdf_path: Local path to the PDF file.
    :return: Extracted text.
    """
    with pdfplumber.open(pdf_path) as pdf:
        text = ''
        for page in pdf.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text

    return text

async def extract_text_from_url(url: str) -> str:
    """
    Extract text and metadata from a URL asynchronously.

    :param url: URL of the website to extract text from.
    :return: Extracted text.
    """
    if not re.match(r'http[s]?://', url):
        url = 'https://' + url

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    doc = Document(html)
                    soup = BeautifulSoup(doc.summary(), 'html.parser')
                    text = soup.get_text(strip=True)
                    return text
                else:
                    print(f"[-] Error fetching URL {url}: {response.status}")
                    return ""
    except Exception as e:
        print(f"[-] Request error fetching URL {url}: {e}")
        return ""

def getMinHashFromFullText(text):
    """
    Returns the MinHash of a given text.

    Parameters:
    text: text from which to get the MinHash
    returns mh: MinHash object of the text
    """
    if text is None:
        print("Received None text input, returning empty MinHash.")
        return MinHash()

    tokens = text.split()
    mh = MinHash()
    for token in tokens:
        mh.update(token.encode('utf8'))
    return mh

def getSimilarityFromMinHashes(mh_a, mh_b):
    """
    Returns the similarity between two given MinHashes.

    Parameters:
    mh_a: MinHash object from the first text
    mh_b: MinHash object from the second text
    returns similarity: a number between 0 and 1, closer to 1 means more similar 
    """
    return mh_a.jaccard(mh_b)

def extract_iocs(text):
    """
    Extracts IP addresses, domains, and hashes from the given text.

    Parameters:
    text: The text to extract IOCs from.

    Returns:
    iocs: Dictionary containing extracted IP addresses, domains, and hashes.
    """
    iocs = {
        'hashes': re.findall(r'\b[a-f0-9]{32,64}\b', text),
        'ip_addrs': re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', text),
        'domains': re.findall(r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:[a-z]{2,})\b', text)
    }
    return iocs


def is_duplicate(new_minhash, existing_minhashes, threshold=0.3):
    """
    Checks if a given MinHash is similar to any MinHash in the existing database.

    Parameters:
    new_minhash: MinHash of the new text
    existing_minhashes: List of MinHashes from the existing database
    threshold: Similarity threshold for considering texts as duplicates

    Returns:
    bool: True if a duplicate is found, False otherwise
    """
    for mh in existing_minhashes:
        similarity = getSimilarityFromMinHashes(new_minhash, mh)
        if similarity > (1 - threshold):  # similarity closer to 1 means more similar
            return True
    return False

def insert_into_db(text, minhash, iocs, link):
    """
    Insert the extracted data into MongoDB.

    Parameters:
    text: The full text of the document.
    minhash: The MinHash object.
    iocs: A dictionary of extracted IOCs.
    link: The link from which the report was extracted.

    Returns:
    None
    """
    print("[+] Getting minhash digest...")
    minhash = getMinHashFromFullText(text)
    minhash_digest = minhash.digest().tolist()

    # Insert the document if it is not a duplicate
    document = {
        "text": text,
        "minhash": minhash_digest,  # Store the digest as a list of integers
        "hashes": iocs['hashes'],
        "ip_addrs": iocs['ip_addrs'],
        "domains": iocs['domains'],
        "date_added": SCRAPING_TIME,
        "url": link
    }
    print("[+] Inserting...")
    collection.insert_one(document)
    print("[+] Document inserted successfully.")

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
            # reconstruct the MinHash object with the stored digest (list of integers)
            mh._hashvalues = record['minhash']  # directly set the hash values
            existing_minhashes.append(mh)
        else:
            print(f"Record with ID {record['_id']} is missing the 'minhash' field and will be skipped.")
    return existing_minhashes


def get_orkl_report(offset=0, limit=1):
    """
    Fetch a specific report from ORKL using pagination.
    
    :param offset: Offset for the API request.
    :param limit: Number of reports to fetch (usually 1).
    :return: The JSON response containing the report data, or an empty list if no data is found.
    """
    params = {
        'limit': limit,
        'offset': offset,
        'order_by': 'created_at',
        'order': 'desc'
    }
    
    response = requests.get(ORKL_API_URL, params=params)
    
    if response.status_code == 200:
        data = response.json().get('data', [])
        if data:
            return data
        else:
            return None  # stop condition when data is null or empty
    else:
        print(f"Error fetching data from ORKL API: {response.status_code}")
        return None

def process_orkl_report(report, existing_minhashes):
    """
    Process a single ORKL report, extract text, IOCs and insert into the database.
    
    :param report: The ORKL report object (as returned by the API).
    :param existing_minhashes: List of minhashes already existing in the DB.
    """
    text = report.get('plain_text')
    
    if not text:
        print(f"[!] ORKL Report {report.get('id')} has no plain text. Skipping.")
        return

    # minhash for deduplication
    print(f"[+] Processing ORKL Report {report.get('id')}")
    new_minhash = getMinHashFromFullText(text)
    
    # duplicate check
    if is_duplicate(new_minhash, existing_minhashes):
        print(f"[!] ORKL Report {report.get('id')} is a duplicate. Skipping.")
        return

    # IOCs
    print(f"[+] Extracting IOCs from ORKL Report {report.get('id')}")
    iocs = extract_iocs(text)
    
    # insertion
    link = f"ORKL Report {report.get('id')}"
    print(f"[+] Inserting ORKL Report {report.get('id')} into the database.")
    insert_into_db(text, new_minhash, iocs, link)
    print(f"[+] ORKL Report {report.get('id')} processed and inserted successfully.")
