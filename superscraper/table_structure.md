# Table Structure Documentation

This markdown file explains the structure of a MongoDB collection containing documents with text, hash representations, and Indicators of Compromise (IOCs). Every document contains an array of IOCs (JSON objects) extracted using [MaliciaLab IOCSearcher](https://github.com/malicialab/iocsearcher).

---

## Document Structure

Each document in the table contains the following fields:

### **_id**
- **Type:** ObjectId
- **Description:** Unique identifier for the document.

---

### **text**
- **Type:** String
- **Description:** The primary text content of the document, which may be analyzed or processed.

---

### **minhash**
- **Type:** Array (128)
- **Description:** A MinHash representation of the `text`, consisting of 128 hash values. Used for similarity comparisons.

---

### **iocs**
- **Type:** Array
- **Description:** A list of Indicators of Compromise (IOCs) extracted from the `text` field using IOCSearcher.

---

## IOC Object Structure

Each IOC object inside the `iocs` array contains the following fields:

### **type**
- **Type:** String
- **Description:** The type of IOC. Possible values include:
  - `fqdn` - Fully Qualified Domain Name (e.g., "example.com").
  - `ip` - IP Address (IPv4 or IPv6).
  - `url` - URL or web address.
  - `email` - Email address.
  - `hash` - File hash (e.g., MD5, SHA1, SHA256).
  - `filepath` - File path in a system.
  - `registry` - Windows Registry key or value.
  - `custom` - Any custom IOC type.

### **value**
- **Type:** String
- **Description:** The raw IOC value (e.g., "google.com" for an `fqdn`).

### **offset**
- **Type:** Int32
- **Description:** The byte offset in the original text where the IOC was found.

### **defanged_value**
- **Type:** String
- **Description:** A "defanged" version of the IOC value, making it safe for display or transmission (e.g., "google[.]com").

---

## Example Document

```json
{
  "_id": "6745abe6b5579c4480f2f55e",
  "text": "This is a lot of text.",
  "minhash": [12345678, 23456789, ..., 98765432],
  "iocs": [
    {
      "type": "fqdn",
      "value": "google.com",
      "offset": 12762,
      "defanged_value": "google[.]com"
    },
    {
      "type": "ip",
      "value": "192.168.1.1",
      "offset": 12904,
      "defanged_value": "192[.]168[.]1[.]1"
    }
  ]
}
