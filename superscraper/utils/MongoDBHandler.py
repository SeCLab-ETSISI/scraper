from pymongo import MongoClient
from datasketch import MinHash
from datetime import datetime

class MongoDBHandler:
    def __init__(self, connection_string, db_name, collection_name):
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def insert_document(self, text, minhash, iocs, link):
        """
        Insert the extracted data into MongoDB.
        """
        print("[+] Getting minhash digest...")
        minhash_digest = minhash.digest().tolist()

        document = {
            "text": text,
            "minhash": minhash_digest,  # Store the digest as a list of integers
            "hashes": iocs['hashes'],
            "ip_addrs": iocs['ip_addrs'],
            "domains": iocs['domains'],
            "date_added": datetime.utcnow(),  # Use UTC time for consistency
            "url": link
        }

        try:
            self.collection.insert_one(document)
            print("[+] Document inserted successfully.")
        except Exception as e:
            print(f"[!] An error occurred while inserting the document: {e}")

    def load_existing_minhashes(self):
        """
        Load existing MinHashes from MongoDB.
        """
        existing_minhashes = []
        try:
            for record in self.collection.find({}, {'minhash': 1}):
                if 'minhash' in record:
                    mh = MinHash()
                    mh._hashvalues = record['minhash']  # Directly set the hash values
                    existing_minhashes.append(mh)
                else:
                    print(f"Record with ID {record['_id']} is missing the 'minhash' field and will be skipped.")
        except Exception as e:
            print(f"[!] Error loading existing MinHashes: {e}")

        return existing_minhashes

    def is_duplicate(self, new_minhash, threshold=0.3):
        """
        Checks if a given MinHash is similar to any MinHash in the existing database.
        """
        existing_minhashes = self.load_existing_minhashes()
        for mh in existing_minhashes:
            similarity = new_minhash.jaccard(mh)
            if similarity > (1 - threshold):  # similarity closer to 1 means more similar
                return True
        return False
