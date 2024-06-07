import json
import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
}


# Replace the page number in the URL
page_num = 1
urls = []

while True:
    url = f"https://www.microsoft.com/en-us/security/blog/wp-json/ms-search/v2/search/?date=any&page={page_num}&s=&sort-by=newest-oldest&threat-intelligence[]=threat-actors"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Error:", response.status_code)
        break

    data = json.loads(response.text)
    
    if len(data["posts"]) > 0:
        for post in data["posts"]:
            if post["title"] != "Promo":
                image_lnk = re.sub('\s+', '', post["html"]).split("imagelink")
                if len(image_lnk)>1:
                    image_lnk = image_lnk[1]
                    urls.append(image_lnk[image_lnk.find('href="')+6:image_lnk.find('"aria-label')])
        page_num += 1
        print(page_num)
    else:
        break
    
urls = list(set(urls))