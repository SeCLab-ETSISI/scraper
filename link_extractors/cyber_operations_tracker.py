import aiohttp
import asyncio
import csv
import os

# List of unreliable sources (newspapers and such)
unreliable_sources = [
    'reuters.com', 'nytimes.com', 'timesofisrael.com', 'arstechnica.com', 'ft.com', 'bloomberg.com',
    'bbc.com', 'wired.com', 'washingtonpost.com', 'spiegel.de', 'npr.org', 'cnn.com', 'theguardian.com',
    'forbes.com', 'abc.net.au', 'politico.com', 'haaretz.com', 'vice.com', 'apnews.com', 'rferl.org',
    'thehackernews.com', 'bleepingcomputer.com', 'theregister.co.uk', 'smh.com.au', 'cbc.ca',
    'zdnet.com', 'nbcnews.com', 'foxnews.com', 'newyorker.com', 'theverge.com', 'scmp.com', 'france24.com',
    'cnbc.com', 'buzzfeednews.com', 'businessinsider.com', 'newsweek.com', 'techcrunch.com',
    'thehill.com', 'telegraph.co.uk', 'ft.com', 'dailymail.co.uk', 'wsj.com', 'latimes.com',
    'rappler.com', 'qz.com', 'itnews.com.au', 'thetimes.co.uk', 'axios.com', 'straitstimes.com',
    'usatoday.com', 'bostonglobe.com', 'newindianexpress.com', 'thedefensepost.com', 'newportri.com',
    'cbsnews.com', 'govinfosecurity.com', 'foreignpolicy.com', 'bloomberg.com', 'thedailybeast.com',
    'arstechnica.com', 'bbc.co.uk', 'independent.co.uk', 'cnet.com', 'zdnet.com', 'ft.com',
    'businessinsider.com', 'techrepublic.com', 'vox.com', 'nbcnews.com', 'theglobeandmail.com'
]

def is_reliable(url):
    # Extract the domain from the URL
    domain = url.split('/')[2]
    # Check if the domain is in the list of unreliable sources
    return domain not in unreliable_sources

async def download_csv(url, filename):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.read()
            with open(filename, 'wb') as file:
                file.write(content)

async def read_and_filter_csv(filename):
    reliable_links = []
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            for key in ['Sources_1', 'Sources_2', 'Sources_3']:
                if key in row and row[key] and is_reliable(row[key]):
                    reliable_links.append(row[key])
    return reliable_links

def delete_file(filename):
    if os.path.exists(filename):
        os.remove(filename)

async def extract_links():
    csv_url = 'https://www.cfr.org/interactive/cyber-operations/export-incidents?_format=csv'
    csv_filename = 'cyber_operations.csv'
    
    # Step 1: Download the CSV file
    await download_csv(csv_url, csv_filename)
    
    # Step 2 & 3: Read and filter the CSV file
    reliable_links = await read_and_filter_csv(csv_filename)
    
    # Step 4: Delete the CSV file
    delete_file(csv_filename)
    
    return reliable_links

extract_links.__name__ = "cyber_operations_tracker_extractor"

if __name__ == "__main__":
    links = asyncio.run(extract_links())
    print(f"Found {len(links)} reliable links:")
    for link in links:
        print(link)
