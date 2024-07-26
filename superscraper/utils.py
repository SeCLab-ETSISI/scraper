import os
import requests
from typing import List
from pymongo import MongoClient
from readability import Document
from bs4 import BeautifulSoup
from datetime import datetime
import hashlib
import pdfplumber

from globals import HEADERS, MONGO_CONNECTION_STRING, MONGO_DATABASE, MONGO_COLLECTION, GH_TOKEN
from metadata import get_metadata

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
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()['commit']['sha'], branch
        elif response.status_code in [401, 403, 404]:
            print(f"[-] Branch {branch} not found or access denied: {response.status_code}")
        else:
            print(f"[-] Error fetching commit SHA for branch {branch}: {response.status_code} - {response.text}")
            response.raise_for_status()
    
    raise ValueError("[?] None of the specified branches were found in the repository.")

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

def extract_pdfs_from_repo(owner: str, repo: str, local_dir: str, branches: List[str], token: str = None) -> None:
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

    sha, valid_branch = get_github_repo_commit_sha(owner, repo, branches, token)
    tree = get_github_repo_tree(owner, repo, sha, token)

    for item in tree:
        if item['type'] == 'blob' and item['path'].endswith('.pdf'):
            file_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{valid_branch}/{item['path']}"
            
            try:
                print(f"\t ╰─[📜] Downloading {item['path']} from {file_url}")
                local_path = os.path.join(repo_dir, os.path.basename(item['path']))
                download_file(file_url, local_path, token)
                save_pdf_to_mongo(local_path)
            except Exception as e:
                print(f"[-] Error processing {file_url}: {e}")

def save_pdf_to_mongo(pdf_path: str):
    """
    Save PDF text and metadata to MongoDB.

    :param pdf_path: Local path to the PDF file.
    """
    with pdfplumber.open(pdf_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()

    pdf_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    metadata = get_metadata(pdf_path)
    document = {
        "pdf_hash": pdf_hash,
        "text": text,
        "date_added": datetime.utcnow(),
        **metadata
    }
    collection.insert_one(document)

def extract_text_from_url(url: str):
    """
    Extract text and metadata from a URL and save to MongoDB.

    :param url: URL of the website to extract text from.
    """
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        doc = Document(response.text)
        soup = BeautifulSoup(doc.summary(), 'html.parser')
        text = soup.get_text()
        metadata = {
            "title": doc.short_title(),
            "url": url,
            "text": text,
            "date_added": datetime.utcnow()
        }
        collection.insert_one(metadata)
    else:
        print(f"[-] Error fetching URL {url}: {response.status_code}")
