import os
import hashlib
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
import re
import nltk
from nltk.corpus import stopwords
from tqdm import tqdm
import pdfplumber

# settings
load_dotenv()
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

def get_mongo_client() -> MongoClient:
    """
    Create and return a MongoDB client using the connection string from the environment variables.

    Returns:
        MongoClient: A MongoDB client instance.
    """
    connection_string = os.getenv("CONNECTION_STRING")
    if not connection_string:
        raise ValueError("CONNECTION_STRING environment variable not found")

    return MongoClient(connection_string)

def get_pdf_text(file_path: str) -> str:
    """
    Extract text from a PDF file.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        str: Extracted text from the PDF.
    """
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error {e}, with file {file_path}")
        return ""
    
    return text


def preprocess_text(text: str) -> str:
    """
    Preprocess the text by converting to lowercase, removing non-printable characters, and stopwords.

    Args:
        text (str): Input text.

    Returns:
        str: Preprocessed text.
    """
    # lowercase and non-printable chars removal
    text = text.lower()
    text = re.sub(r'[^\x20-\x7E\n]', '', text)

    # stopwords removal
    words = text.split()
    words = [word for word in words if word not in stop_words]

    return ' '.join(words)


def insert_to_mongodb(db_name: str, collection_name: str, data: dict) -> None:
    """
    Insert data into MongoDB.

    Args:
        db_name (str): Name of the database.
        collection_name (str): Name of the collection.
        data (dict): Data to be inserted.

    Returns:
        None
    """
    client = get_mongo_client()
    db = client[db_name]
    collection = db[collection_name]
    collection.insert_one(data)
    print(emoji.emojize(':white_check_mark: Document inserted successfully'))


def insert_malware():
    folder_path = os.getcwd()+"/../scraping/csv/malware/"
    malware_df = []
    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            df = pd.read_csv(os.path.join(folder_path, file), delimiter="|")
            df['source'] = file.split("/")[-1].split(".")[0]
            malware_df.append(df)
    malware_df = pd.concat(malware_df)
    # Clean duplicates and add the sources of the malware
    malware_df.dropna(subset=["sha256"], inplace=True)
    deleted_csv_series = malware_df.groupby('sha256')['source'].unique().apply(', '.join)
    malware_df['source'] = malware_df['sha256'].map(deleted_csv_series).fillna('')
    malware_df.drop_duplicates(subset=['sha256'], keep='first', inplace=True)
    for _, row in tqdm(malware_df.iterrows(), total=malware_df.shape[0], desc="Processing PDFs"):
        data = {
            "source": row['source'],
            "path": row['filepath'],
            "sha256": row['sha256'],
        }
        insert_to_mongodb("APTs", "all_malware", data)


def insert_reports():
    folder_path = os.getcwd()+"/../scraping/csv/reports/"
    reports_df = []
    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            df = pd.read_csv(os.path.join(folder_path, file))
            df['source'] = file.split("/")[-1].split(".")[0]
            reports_df.append(df)
    reports_df = pd.concat(reports_df)
    # Clean duplicates and add the sources of the reports
    reports_df.dropna(subset=["sha256"], inplace=True)
    deleted_csv_series = reports_df.groupby('sha256')['source'].unique().apply(', '.join)
    reports_df['source'] = reports_df['sha256'].map(deleted_csv_series).fillna('')
    reports_df.drop_duplicates(subset=['sha256'], keep='first', inplace=True)

    for _, row in tqdm(reports_df.iterrows(), total=reports_df.shape[0], desc="Processing PDFs"):
        pdf_path = row['filepath']
        source = row['source']

        # gathering info from pdf
        pdf_text = get_pdf_text(pdf_path)
        preprocessed_text = preprocess_text(pdf_text)
        data = {
            "source": source,
            "filepath": pdf_path,
            "sha256":  row['sha256'],
            #"original_path": row['original_path'],
            "text": preprocessed_text
        }
        insert_to_mongodb("APTs", "all_reports", data)



if __name__ == "__main__":
    insert_malware()
    insert_reports()
