import os
import pandas as pd
from typing import List, Callable

def get_all_extractors() -> List[Callable[[], List[str]]]:
    """
    Dynamically imports all extractor modules and gathers their extract_links functions.

    :return: A list of extractor functions.
    """
    extractors = []
    for filename in os.listdir(os.path.dirname(__file__)):
        if filename.startswith('extractor') and filename.endswith('.py') and filename != 'extractor_handler.py':
            extractor_module = filename[:-3]  # remove the '.py' extension
            module = __import__(extractor_module)
            if hasattr(module, 'extract_links'):
                extractors.append(module.extract_links)
    return extractors

def remove_duplicates(links: List[str]) -> List[str]:
    """
    Removes duplicate links from the list.

    :param links: A list of links.
    :return: A list of unique links.
    """
    return list(set(links))

def append_to_csv(links: List[str], csv_path: str) -> None:
    """
    Appends unique links to the CSV file.

    :param links: A list of links to append.
    :param csv_path: The path to the CSV file.
    """
    if not os.path.exists(csv_path):
        df = pd.DataFrame(links, columns=['link'])
        df.to_csv(csv_path, index=False)
    else:
        existing_links = pd.read_csv(csv_path)
        all_links = existing_links['link'].tolist() + links
        unique_links = remove_duplicates(all_links)
        df = pd.DataFrame(unique_links, columns=['link'])
        df.to_csv(csv_path, index=False)

def main() -> None:
    """
    Main function to process links from all extractors and append unique links to the CSV file.
    """
    csv_path = '../links/links.csv'
    all_links = []

    extractors = get_all_extractors()
    for extractor in extractors:
        links = extractor()
        all_links.extend(links)

    unique_links = remove_duplicates(all_links)
    append_to_csv(unique_links, csv_path)

if __name__ == "__main__":
    main()
