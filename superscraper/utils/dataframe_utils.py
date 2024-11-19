import logging
from concurrent.futures import as_completed, ThreadPoolExecutor
import os
import pandas as pd
from upsetplot import from_memberships, UpSet
import matplotlib.pyplot as plt
import warnings
from matplotlib import cm

from file_analysis_utils import get_all_file_types
from pymongo import MongoClient
from globals import HEADERS, MONGO_CONNECTION_STRING, MONGO_DATABASE, MONGO_COLLECTION, GH_TOKEN, ORKL_API_URL


# Configure logging
logging.basicConfig(filename='malware_analysis.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def insert_dict_to_mongo(data, db_name, collection_name, mongo_uri=MONGO_CONNECTION_STRING):
    """
    Inserts a dictionary into a MongoDB collection.

    Args:
        data (dict): The dictionary to insert.
        db_name (str): The name of the database.
        collection_name (str): The name of the collection.
        mongo_uri (str): The MongoDB URI.
    
        
    Returns:
        int: The number of documents inserted.
    
    """
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]
    
    # Insert records into the collection
    result = collection.insert_one(data)
    
    return len(result.inserted_id)

def update_mongo_collection(file_details):
    """
    Updates a MongoDB collection with new file details or modifies existing ones.

    Args:
        file_details (dict): The details of the new file.
    """
    client = MongoClient('mongodb://localhost:27017/')
    db = client['your_database_name']
    collection = db['your_collection_name']
    
    sha256 = file_details['sha256']
    existing_entry = collection.find_one({"sha256": sha256})

    if existing_entry:
        # Update the existing entry with new details
        collection.update_one(
            {"sha256": sha256},
            {"$set": file_details}
        )
    else:
        # Insert a new entry if it doesn't exist
        collection.insert_one(file_details)
def index_files(folder_path):
    """
    Indexes files in a given folder and maps filenames to their full paths.

    Args:
        folder_path (str): The path of the folder to index.

    Returns:
        dict: A dictionary mapping filenames to their full paths.
    """
    file_index = {}
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_index[file] = os.path.join(root, file)
    return file_index


def find_file_paths(dataframe, folder_path, field='sha256'):
    """
    Maps each entry in the specified DataFrame field to its file path based on an indexed folder.

    Args:
        dataframe (pd.DataFrame): The DataFrame containing a column to map to file paths.
        folder_path (str): The folder containing the files.
        field (str): The column name in the DataFrame that contains filenames or unique identifiers.

    Returns:
        pd.DataFrame: The modified DataFrame with an additional 'file_path' column.
    """
    file_index = index_files(folder_path)
    dataframe['file_path'] = dataframe[field].map(file_index.get)
    return dataframe


def find_virustotal_reports(dataframe, folder_path, field='sha256'):
    """
    Adds paths to VirusTotal report files for each entry in the DataFrame based on an indexed folder.

    Args:
        dataframe (pd.DataFrame): The DataFrame with a column to map to VirusTotal reports.
        folder_path (str): The folder containing VirusTotal report JSON files.
        field (str): The column name in the DataFrame that contains the identifiers for the reports.

    Returns:
        pd.DataFrame: The modified DataFrame with an additional 'virustotal_reports' column.
    """
    file_index = index_files(folder_path)
    dataframe['virustotal_reports'] = dataframe[field].apply(lambda sha: file_index.get(f"{sha}.json"))
    return dataframe


def generate_df(df, csv_name, sha256_column, filesize_column, apt_group_column, country_column, campaign_column, malware_family_column):
    """
    Generates a standardized DataFrame with common columns for malware datasets.

    Args:
        df (pd.DataFrame): The input DataFrame.
        csv_name (str): The name of the CSV file or dataset.
        sha256_column (str): Column name for the SHA-256 hash.
        filesize_column (str): Column name for file size.
        apt_group_column (str): Column name for APT group.
        country_column (str): Column name for country.
        campaign_column (str): Column name for campaign.
        malware_family_column (str): Column name for malware family.

    Returns:
        pd.DataFrame: The standardized DataFrame.
    """
    return pd.DataFrame({
        "csv_name": [csv_name] * len(df),
        "sha256": df[sha256_column],
        "file_path": df["file_path"],
        "file_paths": df["file_path"],
        "virustotal_reports": df["virustotal_reports"] if "virustotal_reports" in df.columns else None,
        "md5": df["md5"] if "md5" in df.columns else None,
        "sha1": df["sha1"] if "sha1" in df.columns else None,
        "file_size": df[filesize_column] if filesize_column else None,
        "apt_group": df[apt_group_column] if apt_group_column else None,
        "country": df[country_column] if country_column else None,
        "campaign": df[campaign_column] if campaign_column else None,
        "malware_family": df[malware_family_column] if malware_family_column else None
    })


def handle_duplicates(df):
    """
    Handles duplicates in the DataFrame by combining sources and file paths for each unique SHA-256 hash.

    Args:
        df (pd.DataFrame): The DataFrame to deduplicate.

    Returns:
        pd.DataFrame: The deduplicated DataFrame with combined values for each unique SHA-256 hash.
    """
    df = df.groupby('sha256').agg({
        'csv_name': lambda x: ', '.join(str(v) for v in x.unique() if v is not None),
        'file_paths': lambda x: ', '.join(str(v) for v in x if v is not None),
        'file_path': 'first',
        'virustotal_reports': 'first',
        'md5': 'first',
        'sha1': 'first',
        'file_size': lambda x: next((v for v in x if v is not None), None),
        'apt_group': lambda x: ', '.join(str(v) for v in x.unique() if v is not None),
        'country': lambda x: ', '.join(str(v) for v in x.unique() if v is not None),
        'campaign': lambda x: ', '.join(str(v) for v in x.unique() if v is not None),
        'malware_family': lambda x: ', '.join(str(v) for v in x.unique() if v is not None)
    }).reset_index().rename(columns={'csv_name': 'source'})
    
    df['file_path'] = df['file_path'].replace('', None)
    df['file_paths'] = df['file_paths'].replace('', None)
    df['available'] = df['file_path'].notnull()
    return df


def load_all_datasets(base_path='.'):
    """
    Loads, merges, and deduplicates multiple malware datasets based on SHA-256 hash.

    Args:
        base_path (str): The base directory containing the dataset CSV files.

    Returns:
        pd.DataFrame: The merged and deduplicated DataFrame of all datasets.
    """
    dataframes_info = {
        'dapt_binaries': {'csv_name': 'dapt_binaries', 'sha256_column': 'sha256'},
        'vx_underground': {'csv_name': 'vx_underground', 'sha256_column': 'sha256', 'campaign_column': 'campaign', 'file_size_column': 'file_size'},
        'apt_malware': {'csv_name': 'apt_malware', 'sha256_column': 'SHA256', 'apt_group_column': 'APT-group', 'country_column': 'Country'},
        'apt_class': {'csv_name': 'apt_class', 'sha256_column': 'sha256', 'delimiter': '|', 'apt_group_column': 'group', 'country_column': 'nation'},
        'ADAPTDataset': {'csv_name': 'ADAPTDataset', 'sha256_column': 'sha256', 'apt_group_column': 'Normalized_Tag', 'campaign_column': 'Campaign_Tag'}
    }
    
    df_malware_list = []
    for df_name, info in dataframes_info.items():
        file_path = os.path.join(base_path, f"{info['csv_name']}.csv")
        delimiter = info.get('delimiter', ',')
        df = pd.read_csv(file_path, delimiter=delimiter)
        logging.info(f"Loading {df_name}...")

        if df[info['sha256_column']].isnull().sum() > 0:
            logging.warning(f"\tFound null SHA-256 values: {df[info['sha256_column']].isnull().sum()} entries")

        if "ADAPTDataset" in df_name:
            not_apt_bins = df[df["Normalized_Tag"] == "NotAPT"]["sha256"].values
            df = df[~df["sha256"].isin(not_apt_bins)]
        
        if "apt_class" in df_name:
            df = find_virustotal_reports(df, "./virustotal_reports", info['sha256_column'])

        if "vx_underground" not in df_name:
            df = find_file_paths(df, f"./{info['csv_name']}", info['sha256_column'])

        gen_df = generate_df(
            df,
            info['csv_name'],
            info['sha256_column'],
            info.get('file_size_column'),
            info.get('apt_group_column', None),
            info.get('country_column', None),
            info.get('campaign_column', None),
            info.get('malware_family_column', None)
        )

        df_malware_list.append(gen_df)
        logging.info(f"\tLoaded {len(gen_df)} entries; {gen_df['file_path'].isnull().sum()} files missing")

    df_malware = pd.concat(df_malware_list, ignore_index=True).dropna(subset=['sha256'])
    return df_malware

def process_row(index, row):
    """
    Processes a DataFrame row to retrieve file type information from multiple sources.

    Args:
        index (int): The index of the row being processed.
        row (pd.Series): The row data containing at least 'file_path' and 'sha256' columns.

    Returns:
        tuple: A tuple containing the index and the identified file types from Magika, libmagic, and ExifTool.
               If 'file_path' is None, returns None for file types.
    """
    file_path = row.get("file_path")
    sha256 = row.get("sha256")
    
    if file_path:
        magika_type, libmagic_type, exiftool_type = get_all_file_types(file_path, sha256)
        return index, magika_type, libmagic_type, exiftool_type

    return index, None, None, None

# Main execution function to parallelize the row processing
def parallel_process_dataframe(df, max_workers=15):
    """
    Extract file type information from a DataFrame using parallel processing.
    Args:
        df (pd.DataFrame): The DataFrame containing malware information.
        max_workers (int): Maximum number of parallel workers.
    Returns:
        list: List of tuples containing (index, magika_type, libmagic_type, exiftool_type) for each row.
    """
    results = []
    progress_counter = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_row, index, row): index for index, row in df.iterrows()}
        
        for future in as_completed(futures):
            try:
                index, magika_type, libmagic_type, exiftool_type = future.result()
                results.append((index, magika_type, libmagic_type, exiftool_type))
                
                # Track and log progress every 1000 rows processed
                progress_counter += 1
                if progress_counter % 1000 == 0:
                    logging.info(f"Processed {progress_counter} rows")
                    
            except Exception as e:
                logging.error(f"Error processing row {futures[future]}: {e}")
    
    return results

def process_dataframe(df):
    """
    Extract file type information from the DataFrame sequentially (non-parallel).
    Args:
        df (pd.DataFrame): The DataFrame containing malware information.
    Returns:
        list: List of tuples (index, magika_type, libmagic_type, exiftool_type) for each row.
    """
    results = []
    progress_counter = 0
    for index, row in df.iterrows():
        file_path = row["file_path"]
        if file_path:
            magika_type, libmagic_type, exiftool_type = get_all_file_types(file_path, row["sha256"])
            results.append((index, magika_type, libmagic_type, exiftool_type))
        else:
            results.append((index, None, None, None))
        
        # Log progress every 1000 rows
        progress_counter += 1
        if progress_counter % 1000 == 0:
            logging.info(f"Processed {progress_counter} rows")
        
    return results

def add_filetype(df_malware):
    """
    Add file type information columns to the DataFrame based on file type analysis.
    Args:
        df_malware (pd.DataFrame): DataFrame of malware samples.
    Returns:
        pd.DataFrame: Updated DataFrame with added columns for file types.
    """
    df_malware["file_type_magika"] = None
    df_malware["file_type_libmagic"] = None
    df_malware["file_type_exiftool"] = None

    # Parallel processing of DataFrame rows
    results = parallel_process_dataframe(df_malware, max_workers=30)

    # Update DataFrame based on results
    for index, magika_type, libmagic_type, exiftool_type in results:
        df_malware.at[index, "file_type_magika"] = magika_type
        df_malware.at[index, "file_type_libmagic"] = libmagic_type
        df_malware.at[index, "file_type_exiftool"] = exiftool_type
    return df_malware

def generate_venn_diagram(df_malware):
    """
    Generate a Venn diagram showing the distribution of malware samples by source.
    Args:
        df_malware (pd.DataFrame): DataFrame of malware samples.
    """
    warnings.filterwarnings('ignore')
    df = df_malware.copy()
    df['source'] = df['source'].str.split(', ')
    
    # Create membership data for the Venn diagram
    upset_data = from_memberships(
        memberships=[tuple(sorted(sources)) for sources in df['source']],
        data=df.index
    )
    upset = UpSet(upset_data, subset_size='count', show_counts='%d', sort_by='cardinality')
    
    # Configure colors for different subset degrees
    palette = cm.get_cmap("Set2", 5)
    for degree in range(1, 6):
        upset.style_subsets(min_degree=degree, facecolor=palette(degree - 1))

    # Display and save the Venn diagram
    upset.plot()
    plt.savefig("venn_diagram_sources_malware.png", dpi=300, bbox_inches="tight")
    plt.show()

def process_binaries(plot_venn=True):
    """
    Process and analyze malware binary files from various datasets.
    - Loads, merges, and deduplicates datasets.
    - Optionally generates a Venn diagram of sources.
    - Adds file type information to the dataset.
    Args:
        plot_venn (bool): If True, generates a Venn diagram of sources.
    """
    # Load and process datasets
    df_malware = load_all_datasets(base_path="./")
    df_malware = handle_duplicates(df_malware)
    df_malware.reset_index(drop=True, inplace=True)
    
    # Update file paths and add availability status
    df_malware['file_path'] = df_malware['file_path'].replace('', None)
    df_malware['file_paths'] = df_malware['file_paths'].replace('', None)
    logging.info(f"Final DataFrame contains {len(df_malware)} unique samples but there are {df_malware['file_path'].isnull().sum()} missing files")
    df_malware['available'] = df_malware['file_path'].notnull()
    
    # Log summary of binary availability
    logging.info("="*100)
    logging.info("We only have access to the following binaries:\n%s", df_malware["available"].value_counts())
    logging.info("="*40)
    logging.info("Of those we do not have access, they come from:\n%s", df_malware[df_malware["available"] == False]["source"].value_counts())

    # Optional Venn diagram generation
    if plot_venn:
        generate_venn_diagram(df_malware)

    # Add file type data to DataFrame
    df_malware = add_filetype(df_malware)

    # Save DataFrame to a file
    df_malware.to_pickle("malware_df.pkl")
