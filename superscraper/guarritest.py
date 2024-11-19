import re
from pymongo import MongoClient
from globals import HEADERS, MONGO_CONNECTION_STRING, MONGO_DATABASE, MONGO_COLLECTION, GH_TOKEN, ORKL_API_URL, SCRAPING_TIME
import requests

# Initialize MongoDB connection
client = MongoClient(MONGO_CONNECTION_STRING)
db = client[MONGO_DATABASE]
collection = db[MONGO_COLLECTION]

def get_orkl_report(offset=0, limit=1):
    """
    Fetch a specific report from ORKL using pagination.
    :param offset: Offset for the API request.
    :param limit: Number of reports to fetch (usually 1).
    :return: The JSON response containing the report data, or an empty list if no data is found.
    """
    params = {
        'limit': limit,
        'offset': offset,
        'order_by': 'created_at',
        'order': 'desc'
    }
    
    response = requests.get(ORKL_API_URL, params=params)
    
    if response.status_code == 200:
        data = response.json().get('data', [])
        if data:
            return data
        else:
            return None  # stop condition when data is null or empty
    else:
        print(f"Error fetching data from ORKL API: {response.status_code}")
        return None

# Fetch a report from the API
offset = 1
report_data = get_orkl_report(offset=offset, limit=1)

if report_data is None:
    print(f"No more reports found at offset {offset}. Stopping.")
else:
    for report in report_data:
        report_id = report['id']
        print(f"Report ID from API: {report_id}")
        
        # Build regex pattern for the database query
        regex_pattern = re.compile(f"^ORKL Report {report_id}$", re.IGNORECASE)
        
        # Query the database
        db_report = collection.find_one({"url": {"$regex": regex_pattern}})
        
        if db_report:
            print(f"Found matching report in database:\n{db_report}")
        else:
            print(f"No matching report found in the database for ID: {report_id}")

# Close the MongoDB connection
client.close()
