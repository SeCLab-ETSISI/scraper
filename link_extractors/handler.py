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
    unique_links = list(set(links))
    num_duplicates = len(links) - len(unique_links)
    logging.debug(f"Removed {num_duplicates} duplicate links.")
    return unique_links, num_duplicates

async def append_to_csv(links: List[str], csv_path: str, lock: asyncio.Lock) -> None:
    async with lock:  # exclusive access to the CSV file
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
                unique_links, num_duplicates = remove_duplicates(all_links)
                df = pd.DataFrame(unique_links, columns=['link'])
                df.to_csv(csv_path, index=False)
                logging.debug(f"Appended links to existing CSV file, {num_duplicates} duplicates removed in total")
            except pd.errors.EmptyDataError:
                # in case the CSV file exists but is empty
                df = pd.DataFrame(links, columns=['link'])
                df.to_csv(csv_path, index=False)
                logging.debug(f"CSV file was empty. Created new CSV file with links")

async def run_extractor(extractor, lock, all_links):
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
            # sample log of the links for debugging
            logging.debug(f"Sample links: {links[:5]}")
            print(f"Extractor {extractor.__name__} returned {len(links)} links")  # number of links obtained
            
            async with lock:  # ensure safe access to shared resource
                all_links.extend(links)
            return extractor.__name__, links
        else:
            logging.warning(f"Extractor {extractor.__name__} returned no links")
            return extractor.__name__, []
    except Exception as e:
        logging.error(f"Error running extractor {extractor.__name__}: {e}")
        return extractor.__name__, []

async def main() -> None:
    start_time = time.time()
    csv_path = os.path.join(parent_dir, 'links', 'links.csv')  # path to links.csv 
    logging.debug(f"CSV path: {csv_path}")
    
    all_links = []
    extractor_results = {}
    total_duplicates_removed = 0
    lock = asyncio.Lock()  # prevent race conditions

    extractors = await get_all_extractors()  # get all extractor functions
    logging.debug(f"Found {len(extractors)} extractors")

    tasks = [run_extractor(extractor, lock, all_links) for extractor in extractors]
    results = await asyncio.gather(*tasks)

    for extractor_name, links in results:
        extractor_results[extractor_name] = len(links)

    logging.debug(f"Total collected links before removing duplicates: {len(all_links)}")
    
    if all_links:
        unique_links, duplicates_removed = remove_duplicates(all_links)  # remove duplicates from list
        total_duplicates_removed += duplicates_removed
        logging.debug(f"Total unique links: {len(unique_links)}")
        logging.debug(f"Total duplicates removed across all extractors: {total_duplicates_removed}")
        await append_to_csv(unique_links, csv_path, lock)  # append unique links to links.csv
        logging.debug("Completed appending links to CSV")
    else:
        logging.warning("No links were collected from any extractor")

    end_time = time.time()
    total_runtime = end_time - start_time
    logging.debug(f"Total runtime: {total_runtime:.2f} seconds")

    print("Documents extracted by each extractor:")
    print(extractor_results)
    print(f"Total duplicates removed: {total_duplicates_removed}")
    print(f"Total runtime: {total_runtime:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
