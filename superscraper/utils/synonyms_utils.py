import os
import pandas as pd
import requests
import pickle
import re
from bs4 import BeautifulSoup

# Download APT spreadsheet from Google Sheets
def download_apt_spreadsheet(url, output_path="apt_spreadsheet.xlsx"):
    """
    Downloads a spreadsheet from a given URL and saves it locally.

    Args:
        url (str): The URL of the spreadsheet.
        output_path (str): Path to save the downloaded spreadsheet.
    """
    print("Downloading APT spreadsheet...")
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, 'wb') as file:
            file.write(response.content)
        print(f"Spreadsheet downloaded successfully to {output_path}")
    else:
        raise Exception(f"Failed to download spreadsheet. Status code: {response.status_code}")

# Extract sheets into separate files
def extract_sheets_to_folder(excel_file_path, output_folder='sheets'):
    """
    Extracts all sheets from an Excel file into individual files in a specified folder.

    Args:
        excel_file_path (str): Path to the Excel file.
        output_folder (str): Folder to save extracted sheets.
    """
    print("Extracting sheets to folder...")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    excel_data = pd.ExcelFile(excel_file_path)
    for sheet_name in excel_data.sheet_names:
        sheet_data = excel_data.parse(sheet_name)
        output_file_path = os.path.join(output_folder, f"{sheet_name}.xlsx")
        sheet_data.to_excel(output_file_path, index=False)
        print(f"Saved sheet '{sheet_name}' to {output_file_path}")


def search_apt_names(apt_dict, names):
    """
    Searches the APT names dictionary for a given list of names.

    Args:
        apt_dict (dict): APT names dictionary.
        names (list): List of names to search for.
    
    Returns:
        str: Common name of the APT group if found, otherwise None.
    """
    for common_name, info in apt_dict.items():
        if any(name in info["synonyms"] for name in names):
            return common_name
        elif any(name == common_name for name in names):
            return common_name
    return None


def process_microsoft_excel(apt_dict, microsoft_excel_path):
    """
    Updates the APT names dictionary with the Microsoft data from an Excel file.

    Args:
        apt_dict (dict): APT names dictionary.
        microsoft_excel_path (str): Path to the Microsoft Excel file.

    Returns:
        dict: Updated APT names dictionary.
    """
    microsoft_df = pd.read_excel(microsoft_excel_path).dropna(how='all', axis=1).dropna(how='all')
    microsoft_df.columns = microsoft_df.iloc[0]
    microsoft_df = microsoft_df.iloc[1:]
    first_four_columns = microsoft_df.iloc[:, :4].reset_index(drop=True)
    remaining_columns = microsoft_df.iloc[:, 4:].reset_index(drop=True)
    microsoft_df = pd.concat([first_four_columns, remaining_columns], ignore_index=True).dropna(how='all')
    for _, row in microsoft_df.iterrows():
        nation = row["Origin/Threat"].lower().replace(" ", "_")
        names = [row[i] for i in ['Previous name', 'New name', 'Other names'] if pd.notna(row[i])]
        common_name = search_apt_names(apt_dict, names)

        if common_name:
            synonyms = set(apt_dict[common_name]["synonyms"].split(", ") + [row['Previous name'], row['New name']])
            apt_dict[common_name]["synonyms"] = ", ".join(synonyms)
        else:
            apt_dict[row["New name"]] = {"synonyms": ", ".join(names), "operations": [], "nation": nation}
    return apt_dict

# Function to extract APT information
def extract_apt_info(file_path, nation, info):
    """
    Extract APT names and operations from the given Excel file.

    Args:
        file_path (str): Path to the Excel file.
        nation (str): Nation associated with the APT.
        info (dict): Dictionary containing column ranges for APT names and operations.

    Returns:
        dict: Dictionary containing APT names and operations.
    """
    apt_dict = {}
    try:
        # Read the Excel file
        df = pd.read_excel(file_path).dropna(how='all')
    except Exception as e:
        raise Exception(f"Failed to read {file_path}: {e}")
    
    for _, row in df.iloc[1:].iterrows():  # Skip first row
        common_name = row.iloc[0]
        names = row.iloc[info["apt_names"][0]:info["apt_names"][1]].dropna()
        names = ', '.join(map(str, names))
        operations = [row.iloc[i] for i in range(*info["operations"]) if pd.notna(row.iloc[i])]

        set_nation = nation
        if nation == "unknown" and pd.notna(row.iloc[10]):
            set_nation = "unknown"
        elif nation == "middle_east" and pd.notna(row.iloc[8]):
            set_nation = row.iloc[8] if "Lebanon" not in str(row.iloc[8]) else "Suspected Iran"

        apt_dict[common_name] = {"synonyms": names, "operations": operations, "nation": set_nation}
    return apt_dict


def process_apt_spreadsheet(sheets_folder):
    """
    Processes the APT spreadsheet to extract APT names and operations.

    Args:
        sheets_folder (str): Folder containing the extracted sheets.
    
    Returns:
        dict: Dictionary containing APT names and operations
    
    """
    apt_info_dict = {
        'China': {'apt_names': [0, 12], 'operations': [13, 16]},
        'Iran': {'apt_names': [0, 11], 'operations': [12, 14]},
        'Israel': {'apt_names': [0, 4], 'operations': [5, 6]},
        'Middle East': {'apt_names': [0, 4], 'operations': [5, 7]},  
        'NATO': {'apt_names': [0, 7], 'operations': [8, 11]},
        'North Korea': {'apt_names': [0, 13], 'operations': [14, 23]},
        'Others': {'apt_names': [0, 8], 'operations': [9, 11]},  
        'Russia': {'apt_names': [0, 15], 'operations': [16, 22]},
        'Unknown': {'apt_names': [0, 4], 'operations': [5, 7]},
    }
    apt_names_dict = {}
    
    # Extract APT information from each relevant Excel file
    for nation, info in apt_info_dict.items():
        xlsx_path = os.path.join(sheets_folder, f"{nation}.xlsx")
        apt_names_dict.update(extract_apt_info(xlsx_path, nation, info))
    
    microsoft_excel_path = os.path.join(sheets_folder, "Microsoft 2023 renaming taxonom.xlsx")
    apt_names_dict = process_microsoft_excel(apt_names_dict, microsoft_excel_path)

    return apt_names_dict

# Fetch actors from Malpedia
def fetch_malpedia_actors(url):
    """
    Scrapes Malpedia to extract threat actor information.

    Args:
        url (str): URL of the Malpedia actors page.

    Returns:
        dict: Threat actor data including names, synonyms, and country information.
    """
    country_mapping = {
        "ru": "Russia", "cn": "China", "ir": "Iran", "kp": "North Korea",
        "tr": "Turkey", "kr": "South Korea", "in": "India", "pk": "Pakistan",
        "il": "Israel", "us": "United States", "lb": "Lebanon", "sy": "Syria",
        "ng": "Nigeria", "by": "Belarus", "fr": "France", "br": "Brazil",
        "iq": "Iraq", "ke": "Kenya", "es": "Spain", "vi": "Vietnam",
        "tn": "Tunisia", "at": "Austria", "my": "Malaysia", "ro": "Romania",
        "ps": "Palestina", "id": "Indonesia", "ka": "Kazakhstan"
    }
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.find_all('tr', class_='clickable-row')

    actors = {}
    for row in rows:
        common_name = row.find('td', class_='common_name').text.strip()
        synonyms = row.find('td', class_='synonyms').text.strip() if row.find('td', class_='synonyms') else ""
        synonyms = synonyms.replace('Subgroup: ', ', ')
        country_span = row.find('td', class_='country').find('span')
        country_code = country_span['title'] if country_span else "Unknown"
        country_name = country_mapping.get(country_code, "Unknown")

        actors[common_name] = {
            'synonyms': common_name + ", " + synonyms,
            'country': country_name
        }
    return actors


# Fetch actors from MITRE ATT&CK
def fetch_mitre_actors(url):
    """
    Scrapes MITRE ATT&CK to extract threat actor information.

    Args:
        url (str): URL of the MITRE ATT&CK groups page.

    Returns:
        dict: Threat actor data including names and synonyms.
    """
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', class_='table')
    rows = table.find('tbody').find_all('tr')

    actors = {}
    for row in rows:
        columns = row.find_all('td')
        if len(columns) >= 3:
            actors[columns[0].text.strip()] = {
                'synonyms': columns[0].text.strip() + ", " + columns[1].text.strip() + ", " + columns[2].text.strip()
            }
    return actors
    
# Process EternalLiberty CSV
def process_ethernal_csv(file_path):
    """
    Processes EternalLiberty CSV file to extract threat actor data.

    Args:
        file_path (str): Path to the EternalLiberty CSV file.

    Returns:
        dict: Threat actor data including names, synonyms, and country information.
    """
    ethernal = pd.read_csv(file_path)
    actors = {}
    for _, row in ethernal.iterrows():
        synonyms = []
        for col in ethernal.columns[4:]:
            if pd.notna(row[col]):
                double_name = row[col].split('/')
                synonyms.extend(double_name if len(double_name) > 1 else [row[col]])

        actors[row["Threat Actor Official Name"]] = {
            'synonyms': row["Threat Actor Official Name"] + ", " + ', '.join(synonyms),
            'country': row['Country'] if pd.notna(row['Country']) else "Unknown"
        }
    return actors

# Merge actors from various sources
def merge_actors(merged_apts_alias, actors_dict_to_add, source_name):
    """
    Merges actors from multiple sources into a unified dictionary.

    Args:
        merged_apts_alias (dict): Existing merged dictionary of actors.
        actors_dict_to_add (dict): New actors to be merged.
        source_name (str): Name of the source being merged.

    Returns:
        tuple: Updated dictionary and number of conflicts encountered.
    """
    new_rows_apt_alias = {}
    counter_duplicates_conflict = []

    for common_name_to_add, details_to_add in actors_dict_to_add.items():
        synonyms_to_add = set(re.split(r', |,', details_to_add["synonyms"]))
        country_to_add = details_to_add.get('country', 'Unknown')
        found_match = False

        for common_name_merged, details_merged in merged_apts_alias.items():
            intersection = details_merged["synonyms"].intersection(synonyms_to_add)
            if common_name_to_add == common_name_merged or (intersection != {''} and len(intersection) > 0):
                if found_match:
                    counter_duplicates_conflict.append(common_name_to_add)
                found_match = common_name_merged
                merged_apts_alias[common_name_merged]['synonyms'].update(synonyms_to_add)
                if country_to_add not in details_merged['nation']:
                    merged_apts_alias[common_name_merged]['nation'].add(country_to_add)

        if not found_match:
            new_rows_apt_alias[common_name_to_add] = {
                "synonyms": synonyms_to_add,
                "operations": set(),
                "nation": {country_to_add}
            }

    merged_apts_alias.update(new_rows_apt_alias)
    merged_apts_alias.pop('?', None)

    for common_name, details in merged_apts_alias.items():
        if details["synonyms"]:
            details["synonyms"].discard("")
            merged_apts_alias[common_name]["synonyms"] = details["synonyms"]

    return merged_apts_alias, len(counter_duplicates_conflict)

# Count unique synonyms
def get_unique_synonyms(apts_alias):
    """
    Counts unique synonyms from the merged dictionary.

    Args:
        apts_alias (dict): Merged dictionary of APTs.

    Returns:
        set: Set of unique synonyms.
    """
    list_all_synonyms = set()
    for common_name, info in apts_alias.items():
        if info['synonyms']:
            list_all_synonyms.update(info['synonyms'])
    return set(list_all_synonyms)


