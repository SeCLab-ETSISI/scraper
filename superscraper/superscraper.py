import os, re
import aiohttp
import asyncio
from typing import List
from pymongo import MongoClient
from readability import Document
from bs4 import BeautifulSoup
from datetime import datetime
import pdfplumber
from datasketch import MinHash

from globals import HEADERS, MONGO_CONNECTION_STRING, MONGO_DATABASE, MONGO_COLLECTION, GH_TOKEN, ORKL_API_URL
from metadata import get_metadata

client = MongoClient(MONGO_CONNECTION_STRING)
db = client[MONGO_DATABASE]
collection = db[MONGO_COLLECTION]

async def get_github_repo_commit_sha(owner: str, repo: str, branches: List[str], token: str) -> str:
    """
    Asynchronously get the SHA of the latest commit on the specified branches of a GitHub repository.

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

    async with aiohttp.ClientSession() as session:
        for branch in branches:
            url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}"
            print(f"Fetching branch info from URL: {url}")  # Debugging statement
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    json_response = await response.json()
                    return json_response['commit']['sha'], branch
                elif response.status in [401, 403, 404]:
                    print(f"[-] Branch {branch} not found or access denied: {response.status}")
                else:
                    print(f"[-] Error fetching commit SHA for branch {branch}: {response.status}")
                    await response.text()

    raise ValueError("[?] None of the specified branches were found in the repository.")

async def get_github_repo_tree(owner: str, repo: str, sha: str, token: str) -> List[dict]:
    """
    Asynchronously get the entire tree of a GitHub repository.

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

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                json_response = await response.json()
                return json_response.get('tree', [])
            else:
                print(f"[-] Error fetching repository tree: {response.status}")
                await response.text()

async def download_file(url: str, local_path: str, token: str = None) -> None:
    """
    Asynchronously download a file from a URL to a local path.

    :param url: URL of the file to download.
    :param local_path: Local path to save the downloaded file.
    :param token: GitHub personal access token for authentication.
    """
    headers = {'Authorization': f'token {token}'} if token else {}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                with open(local_path, 'wb') as file:
                    content = await response.read()
                    file.write(content)
            else:
                print(f"[-] Error downloading file: {response.status}")
                await response.text()

async def extract_pdfs_from_repo(owner: str, repo: str, local_dir: str, branches: List[str], token: str = None) -> None:
    """
    Asynchronously extract all PDF files from a GitHub repository and save them locally.

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
            break  # Stop if a valid branch is found
        except ValueError as e:
            print(f"[-] Error finding branch '{branch}': {e}")
    
    if not sha:
        print(f"[-] No valid branches found in {repo}.")
        return

    tree = await get_github_repo_tree(owner, repo, sha, token)
    
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
                await download_file(file_url, local_path, token)
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
    Asynchronously extract text and metadata from a URL.

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
        'domains': re.findall(r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b', text),
    }
    return iocs

def insert_into_db(text, minhash, iocs, repo_name):
    """
    Inserts data into the MongoDB collection.

    Parameters:
    text: Extracted text from a file or web page.
    minhash: MinHash of the text.
    iocs: Extracted IOCs from the text.
    repo_name: Name of the repository where the text was found.
    """
    doc = {
        'repo_name': repo_name,
        'text': text,
        'minhash': minhash.digest(),
        'iocs': iocs,
        'created_at': datetime.utcnow()
    }
    collection.insert_one(doc)
    print(f"[+] Inserted document into the database for repo {repo_name}")
