# Scraping

This repository contains data and scripts for scraping and extracting APTs malware and reports from various sources.

## Folder Structure

Formally the structure is:

```txt
.
├── LICENSE
├── README.md
├── requirements.txt
├── link_extractors
├── links
│   └── links.csv
└── superscraper
    ├── globals.py
    ├── metadata.py
    ├── superscraper.py
    └── utils.py
```

## Folder Descriptions

- **link_extractors/** contains extractors for webs that contain multiple reports (and each report has its own URL). Each website needs a different extractor since they have different structures.

- **links/** should contain each individual repor's links. It was separated into a different folder in order to allow the possibility of making separate .csv files for different providers.

- **superscraper/** contains the necessary scripts in order to extract text and metadata from pdf files or URLs, and store them in a MongoDB database. 


## How to Use

It is recommended to create a virtual environment to install the correct dependencies and avoid conflicts:
```sh
python3 -m venv my-virtual-environment
pip install -r requirements.txt
```
The `.env` file located in the `superscraper` directory must be set to the relevant MongoDB constants.

The `superscraper.py` script, in the `superscraper` directory, will crawl over the `links.csv` file, extracting information from every single one of them. Two behaviours may occur:

  * **Encountering a GitHub repository (meta-source)**: they normally contain .pdf files, so every pdf file contained in the repository is downloaded, and has is text and metadata extracted. 

  * **Encountering an individual report's URL**: the report's text is extracted and inserted into MongoDB along with some relevant metadata.


# WIP

* Increasing the number of link extractors to introduce more data into the csv files




## Contribute
Text extraction functions for pdf files and URLs are designed to be generic. Both efficiency upgrades and link extractors for specific vendors are welcome.

The structure for a link extractor must be as follows:

```py
def <provider>_link_extractor(blog_url: str):
  """
  extractor code
  """
```

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

# Acknowledgements

This software has been created as part of the project "Improving Malware Attribution with Machine Learning"  (C127/23), a collaboration between the Instituto Nacional de Ciberseguridad (INCIBE) and Universidad Politécnica de Madrid. This initiative is part of the Recovery, Transformation, and Resilience Plan funded by the European Union (Next Generation).

![Banner](https://i.imgur.com/XYZ.png)