import requests
from bs4 import BeautifulSoup

def get_metadata_from_url(url):
    """
    Gets metadata from a given URL.
    
    :param url: URL from which metadata is to be extracted.
    :return: A dictionary with all metadata extracted.
    """
    metadata = {}
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        metas = soup.find_all('meta')

        for meta in metas:
            if 'name' in meta.attrs:
                if meta.attrs["name"] == "keywords":
                    metadata["keywords"] = meta.attrs["content"]
                elif meta.attrs["name"] == "description":
                    metadata["description"] = meta.attrs["content"]
                elif meta.attrs["name"] == "author":
                    metadata["author"] = meta.attrs["content"]
                elif meta.attrs["name"] == "site_name":
                    metadata["siteName"] = meta.attrs["content"]
                elif meta.attrs["name"] == "title":
                    metadata["title"] = meta.attrs["content"]
                elif meta.attrs["name"] == "url":
                    metadata["url"] = meta.attrs["content"]
                elif meta.attrs["name"] == "creation_date":
                    metadata["creation_date"] = meta.attrs["content"]
                elif meta.attrs["name"] == "modified_date":
                    metadata["modified_date"] = meta.attrs["content"]
                elif meta.attrs["name"] == "article:section":
                    metadata["article_section"] = meta.attrs["content"]

        # Open Graph metadata
        og_metas = {
            "og:site_name": "siteName",
            "og:title": "title",
            "og:url": "url",
            "og:description": "ogDescription",
            "og:image": "ogImage",
            "article:author": "articleAuthor",
            "article:section": "articleSection",
            "article:published_time": "articlePublishedTime",
            "article:modified_time": "articleModifiedTime"
        }

        for og_meta, meta_key in og_metas.items():
            tag = soup.find("meta", property=og_meta)
            if tag:
                metadata[meta_key] = tag.attrs.get("content")

    return metadata
