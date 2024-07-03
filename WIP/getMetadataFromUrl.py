import requests
from bs4 import BeautifulSoup

def getMetadataFromUrl2(url):

        """
    Gets metadata from a given URL
 
    :param url: url from which metadata is to be extracted

    returns a dict with all metadata extracted
    """
  
  dic = {}
  response = requests.get(url)
  
  if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    metas = soup.find_all('meta')
    print(len(metas))

    for meta in metas :
     if 'name'  in meta.attrs:
      if meta.attrs["name"] == "keywords":
        dic["keywords"] = meta.attrs["content"]
      if meta.attrs["name"]  == "description":
       dic["description"] = meta.attrs["content"]
      if meta.attrs["name"] == "author":
        dic["author"] = meta.attrs["content"]
      if meta.attrs["name"] == "site_name":
        dic["siteName"] = meta.attrs["content"]
      if meta.attrs["name"] == "title":
        dic["title"] = meta.attrs["content"]
      if meta.attrs["name"] == "url":
        dic["url"] = meta.attrs["content"]
      if meta.attrs["name"] == "creation_date":
        dic["creation_date"] = meta.attrs["content"]
      if meta.attrs["name"] == "modified_date":
        dic["modified_date"] = meta.attrs["content"]
      if meta.attrs["name"] == "article:section":
        dic["article_section"] = meta.attrs["content"]

    keywords = soup.find("meta", property="keywords")
    if(keywords):
      dic["keywords"] = keywords.attrs["content"]
    description = soup.find("meta", property="description")
    if(description):
      dic["description"] = description.attrs["content"]
      print("")
    siteName = soup.find("meta", property="og:site_name")
    if(siteName):
      dic["siteName"] = siteName.attrs["content"]
    title = soup.find("meta", property="og:title")
    if(title):
      dic["title"] = title.attrs["content"]
    url = soup.find("meta", property="og:url")
    if(url):
      dic["url"] = url.attrs["content"]
    ogDescription = soup.find("meta", property="og:description")
    if(ogDescription):
      dic["ogDescription"] = ogDescription.attrs["content"]
    ogImage = soup.find("meta", property="og:image")
    if(ogImage):
      dic["ogImage"] = ogImage.attrs["content"]
    articleAuthor = soup.find("meta", property="article:author")
    if(articleAuthor):
      dic["articleAuthor"] = articleAuthor.attrs["content"]
    articleSection = soup.find("meta", property="article:section")
    if(articleSection):
      dic["articleSection"] = articleSection.attrs["content"]
    articlePublishedTime = soup.find("meta", property="article:published_time")
    if(articlePublishedTime):
      dic["articlePublishedTime"] = articlePublishedTime.attrs["content"]
    articleModifiedTime = soup.find("meta", property="article:modified_time")
    if(articleModifiedTime):
      dic[" articleModifiedTime"] =  articleModifiedTime.attrs["content"]

    return dic
