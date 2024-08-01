import os
import sys
import pandas as pd
from typing import List, Callable, Any
import logging
import importlib
import asyncio
import time

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# python path fixes
script_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
sys.path.append(parent_dir)

async def get_all_extractors() -> List[Callable[[], List[str]]]:
    extractors = []
    extractors_dir = os.path.join(script_dir)
    logging.debug(f"Extractors directory: {extractors_dir}")

    for filename in os.listdir(extractors_dir):
        logging.debug(f"Checking file: {filename}")
        
        if filename.endswith('.py') and filename != 'handler.py':
            extractor_module = filename[:-3]  # handle .py extension
            module_path = f'{extractor_module}'
            
            try:
                module = importlib.import_module(module_path)  # dynamic import
                logging.debug(f"Imported module: {module_path}")
                
                if hasattr(module, 'extract_links'):
                    extractors.append(module.extract_links)  # get each extract_links function and add it to list
                    logging.debug(f"Added extract_links from module: {extractor_module}")
                else:
                    logging.warning(f"Module {module_path} does not have 'extract_links' function")
            except Exception as e:
                logging.error(f"Error importing module {module_path}: {e}")
    
    return extractors

def remove_duplicates(links: List[str]) -> List[str]:
    return list(set(links))

async def append_to_csv(links: List[str], csv_path: str) -> None:
    logging.debug(f"Appending to CSV at: {csv_path}")
    
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        # create a new CSV file if it doesn't exist
        df = pd.DataFrame(links, columns=['link'])
        df.to_csv(csv_path, index=False)
        logging.debug(f"Created new CSV file with links")
    else:
        try:
            existing_links = pd.read_csv(csv_path)
            all_links = existing_links['link'].tolist() + links
            unique_links = remove_duplicates(all_links)
            df = pd.DataFrame(unique_links, columns=['link'])
            df.to_csv(csv_path, index=False)
            logging.debug(f"Appended links to existing CSV file")
        except pd.errors.EmptyDataError:
            # in case the CSV file exists but is empty
            df = pd.DataFrame(links, columns=['link'])
            df.to_csv(csv_path, index=False)
            logging.debug(f"CSV file was empty. Created new CSV file with links")

async def run_extractor(extractor):
    try:
        logging.debug(f"Running extractor {extractor.__name__}")
        start_time = time.time()
        if asyncio.iscoroutinefunction(extractor):
            links = await extractor()
        else:
            loop = asyncio.get_event_loop()
            links = await loop.run_in_executor(None, extractor)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.debug(f"Extractor {extractor.__name__} ran for {elapsed_time:.2f} seconds")

        if links:
            logging.debug(f"Extractor {extractor.__name__} returned {len(links)} links")
            print(f"Extractor {extractor.__name__} returned {len(links)} links")  # number of links obtained
            return extractor.__name__, links
        else:
            logging.warning(f"Extractor {extractor.__name__} returned no links")
            return extractor.__name__, []
    except Exception as e:
        logging.error(f"Error running extractor {extractor.__name__}: {e}")
        return extractor.__name__, []

async def main() -> None:
    csv_path = os.path.join(parent_dir, 'links', 'links.csv')  # path to links.csv 
    logging.debug(f"CSV path: {csv_path}")
    
    all_links = []
    extractor_results = {}

    extractors = await get_all_extractors()  # get all extractor functions
    logging.debug(f"Found {len(extractors)} extractors")

    tasks = [run_extractor(extractor) for extractor in extractors]
    results = await asyncio.gather(*tasks)

    for extractor_name, links in results:
        if links:
            all_links.extend(links)  # append links to the all_links list
        extractor_results[extractor_name] = len(links)

    if all_links:
        unique_links = remove_duplicates(all_links)  # remove duplicates from list
        logging.debug(f"Total unique links: {len(unique_links)}")
        await append_to_csv(unique_links, csv_path)  # append unique links to links.csv
        logging.debug("Completed appending links to CSV")
    else:
        logging.warning("No links were collected from any extractor")

    print("Documents extracted by each extractor:")
    print(extractor_results)

if __name__ == "__main__":
    asyncio.run(main())
