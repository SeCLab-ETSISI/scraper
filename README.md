# Scraping

This repository contains data and scripts for scraping and extracting APTs malware and reports from various sources.

## Folder Structure

./csv:

   ./csv/malware:

      APTMalware.csv

      vx\_underground.csv

   ./csv/reports:

      APT\_REPORT.csv

      vx\_underground.csv

./scrapesr:

   github\_scraper.sh

   vx\_underground\_scraper.sh

./github:

   APT\_REPORT/

   /vx\_underground/

./malware:

   003da3a1e5c69e11bacb2a3b4d9994cdad6b5cc866917a3389de7a16ecf6e88e

./reports:

   1231a3a1e5c69e11bacb2a3b4d9994cdad6b5cc866917a3389de7a16e1312371.pdf


Formally the structure is:

```txt
scraping/
  ├── malware/
  ├── reports/
  ├── scrapers/
  └── csv/
      ├── malware/            <------
      └── reports/            <------
          ├── Source_1/
          ├── ...
          └── Source_N/

```

## Folder Descriptions

- **malware/**: This folder contains unique APTs malware samples extracted from various sources. Each filename is the computed sha256 of the file.

- **reports/**: This folder contains APTs reports extracted from various sources. Each filename is the computed sha256 of the file.

- **csv/**: This folder contains two folders with different CSV files with information of the malware and the extracted reports.
  - **malware/**: Contains a CSV file per source of malware data. The CSV format is as follows:
    - `filepath`: Path to the malware file.
    - `sha256`: SHA-256 hash of the malware file.
    - `campaign`: Campaign associated with the malware.
    - `year`: Year of the malware campaign.
    - `original_path`: Original path from where the malware was sourced.
    - `original_name`: Original name of the malware file.
  - **reports/**: Contains a CSV file per source of malware data. The CSV format is as follows:
    - `report_name`: Name of the report.
    - `filepath`: Path to the report file.
    - `sha256`: SHA-256 hash of the report file.
    - `campaign`: Campaign associated with the report.
    - `year`: Year of the report.
    - `original_path`: Original path from where the report was sourced.

- **Source_1/**, ..., **Source_N/**: These folders contain the extracted data from each source.

- **Scrapers/**: This folder contains the scraping scripts for extracting data from different sources.


## How to Use
The `launch.sh` script, in the `scraping` directory, will launch every script in that directory.

New scrapers (scripts) must add the following data to generated csv files:

```txt
filepath|sha256|md5|sha1|campaign|year|original_path|original_name
```

Using the pipe (`|`) character as a separator.

# WIP

* Making scrapers (other than github_scraper.sh) introduce data into the csv files
* An insert script which reads from .csv files and inserts data into mongodb


## Contribute

### Commit && PR Messages

Messages should follow this format:
```txt
[MODULE][FIX|ADD|DELETE] Summary of modifications
```

#### Example

```txt
* [README][ADD] Execution && Component diagram
* [SCRAPERS][ADD] MITRE scraper
* [RUN_SCRAPERS][DELETED]
* [SCRAPER][FIX] Folder creation bug
```