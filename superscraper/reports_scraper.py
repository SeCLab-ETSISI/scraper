import pandas as pd
import asyncio
import re
from pymongo import MongoClient
from datetime import datetime
from utils.utils import (
    extract_pdfs_from_repo,
    extract_text_from_url,
    extract_iocs,
    insert_into_db,
    load_existing_minhashes_from_db,
    get_orkl_report,
    process_orkl_report,
    is_github_url
)
from globals import (
    GH_TOKEN, SCRAPING_TIME, MONGO_CONNECTION_STRING, MONGO_DATABASE, CLASSIC_TOKEN
)

def validate_github_token():
    """Ensure the GitHub token is set."""
    if GH_TOKEN is None:
        raise ValueError("GitHub token is None.")

def filter_links_by_date(links_file, target_date):
    """
    Read and filter links based on the target date.

    Args:
        links_file (str): Path to the CSV file with links.
        target_date (str): Target date in the format YYYY/MM/DD.

    Returns:
        pd.DataFrame: Filtered DataFrame containing links for the target date.
    """
    links_df = pd.read_csv(links_file)
    links_df.columns = links_df.columns.str.strip()
    print(links_df)

    if 'date' not in links_df.columns:
        raise KeyError("The 'date' column is missing from the CSV file.")


    links_df['date'] = pd.to_datetime(links_df['date'], format="%Y/%m/%d")
    today_date = datetime.strptime(target_date, "%Y/%m/%d")
    return links_df[links_df['date'] == today_date]


async def process_single_link(link, existing_minhashes, mongo_client):
    """
    Process a single link by extracting data and inserting it into the database.

    Args:
        link (str): URL or GitHub repo link.
        existing_minhashes (set): Set of existing MinHashes to avoid duplication.
        mongo_client: MongoDB client instance.
    """
    if is_github_url(link):
        # Use regular expression to match the owner and repo regardless of the URL format
        match = re.match(r'https://github.com/([^/]+)/([^/]+)', link)
        if match:
            owner, repo = match.groups()
            print(f"Using owner: {owner} for repo: {repo}")
            await extract_pdfs_from_repo(owner, repo, '../pdf_files', branches=["main", "master"], token=CLASSIC_TOKEN)
            print(f"[+] Processed GitHub repo {link}")
        else:
            print("[-] Invalid GitHub URL format.")
    else:
        text = await extract_text_from_url(link)
        if text:
            iocs = extract_iocs(text)
            insert_into_db(text, existing_minhashes, iocs, link)
            return True
    return False

async def process_links(links_df, existing_minhashes, mongo_client):
    """
    Process all links from the DataFrame.

    Args:
        links_df (pd.DataFrame): DataFrame with links to process.
        existing_minhashes (set): Set of existing MinHashes.
        mongo_client: MongoDB client instance.
    """
    failed_texts = 0
    successful_texts = 0

    for i, row in enumerate(links_df.itertuples(), start=1):
        link = row.link.strip()
        print(f"------ Processing link {i}: {link}")
        success = await process_single_link(link, existing_minhashes, mongo_client)
        if success:
            successful_texts += 1
        else:
            failed_texts += 1

    print(f"[!] Failed inserts: {failed_texts}")
    print(f"[!] Successful inserts: {successful_texts}")

async def process_orkl_reports(existing_minhashes):
    """
    Process ORKL reports and update the database.

    Args:
        existing_minhashes (set): Set of existing MinHashes.
    """
    print("------ Processing ORKL reports ------")
    offset = 0
    while True:
        reports = get_orkl_report(offset=offset, limit=1)
        if not reports:
            print(f"No more reports found at offset {offset}. Stopping.")
            break
        for report in reports:
            process_orkl_report(report, existing_minhashes)
        offset += 1

async def process_reports(mongo_client):
    """
    Main function to process reports and links.

    Args:
        mongo_client: MongoDB client instance.
    """
    validate_github_token()
    links_df = filter_links_by_date('../links/links.csv', SCRAPING_TIME)

    if links_df.empty:
        print("[!] No links to process for today.")
        return

    existing_minhashes = load_existing_minhashes_from_db()

    # Process links
    await process_links(links_df, existing_minhashes, mongo_client)

    # Process ORKL reports
    await process_orkl_reports(existing_minhashes)

def main():
    """Main entry point for the script."""
    with MongoClient(MONGO_CONNECTION_STRING) as mongo_client:
        asyncio.run(process_reports(mongo_client))

if __name__ == "__main__":
    main()
