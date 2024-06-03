from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from typing import List, Dict, Any


# environment variables and constants
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'data-analysis', '.env')
load_dotenv(dotenv_path)

CONNECTION_STRING = os.getenv("CONNECTION_STRING")
ORKL_URL = "https://archive.orkl.eu/"
DATABASE_NAME = "APTs"
COLLECTION_NAME = "tagged_reports"

def get_json_filenames(url: str) -> List[str]:
    """
    Extract JSON file names from the HTML page.

    Parameters:
    url (str): The URL of the file repository.

    Returns:
    List[str]: A list of JSON file names.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    json_files = []
    for a in soup.find_all('a', class_='file'):
        href = a.get('href')
        if href.endswith('.json'):
            json_files.append(href)
    return json_files


def fetch_json_file(file_url: str) -> Dict[str, Any]:
    """
    Fetch JSON content from a given file URL.

    Parameters:
    file_url (str): The URL of the JSON file.

    Returns:
    Dict[str, Any]: The content of the JSON file.
    """
    response = requests.get(file_url)
    return response.json()


def store_in_mongodb(data: Dict[str, Any], db_name: str, collection_name: str) -> None:
    """
    Store JSON data in MongoDB.

    Parameters:
    data (Dict[str, Any]): The JSON data to store.
    db_name (str): The name of the database.
    collection_name (str): The name of the collection.
    """
    client = MongoClient(CONNECTION_STRING)
    db = client[db_name]
    collection = db[collection_name]
    collection.insert_one(data)


def main() -> None:
    """
    Main function to extract and store all JSON files in MongoDB.
    """
    json_filenames = get_json_filenames(ORKL_URL)
    for filename in json_filenames:
        file_url = f"{ORKL_URL}{filename}"
        json_data = fetch_json_file(file_url)
        store_in_mongodb(json_data, DATABASE_NAME, COLLECTION_NAME)
        print(f"[📁] Stored {filename} in MongoDB")



if __name__ == "__main__":
    main()
