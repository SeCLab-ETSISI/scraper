import os
import requests
from typing import List

def get_github_repo_tree(owner: str, repo: str, token: str, branch: str = "main") -> List[dict]:
    """
    Get the entire tree of a GitHub repository.

    :param owner: Owner of the repository.
    :param repo: Name of the repository.
    :param token: GitHub personal access token for authentication.
    :param branch: Branch to fetch the tree from (default is main).
    :return: List of all files and directories in the repository.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    headers = {'Authorization': f'token {token}'}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        tree = response.json().get('tree', [])
        return tree
    else:
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

    with open(local_path, 'wb') as file:
        file.write(response.content)

def extract_pdfs_from_repo(owner: str, repo: str, local_dir: str, branch: str = "main", token: str = None) -> None:
    """
    Extract all PDF files from a GitHub repository and save them locally.

    :param owner: Owner of the repository.
    :param repo: Name of the repository.
    :param local_dir: Local directory to save the PDF files.
    :param branch: Branch to fetch the content from (default is main).
    :param token: GitHub personal access token for authentication.
    """
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    tree = get_github_repo_tree(owner, repo, token, branch)

    for item in tree:
        if item['type'] == 'blob' and item['path'].endswith('.pdf'):
            file_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{item['path']}"
            print(f"[+] Downloading {item['path']} from {file_url}")
            local_path = os.path.join(local_dir, os.path.basename(item['path']))
            download_file(file_url, local_path, token)


if __name__ == "__main__":
    owner = "blackorbird"
    repo = "APT_REPORT"
    local_dir = "./pdf_files"
    token = "your_github_token" 

    extract_pdfs_from_repo(owner, repo, local_dir, branch="main", token=token)
