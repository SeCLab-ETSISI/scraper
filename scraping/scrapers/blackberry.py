import requests
import json

titles_and_urls = []
page_num = 1
while True:
    url = f"https://blogs.blackberry.com/bin/blogs?page={page_num}&category=https://blogs.blackberry.com/en/category/research-and-intelligence&locale=en"
    response = requests.get(url)
    try:
        if response.status_code == 200:
            data = json.loads(response.text)
            if len(data)==0:
                break
            else:
                print(page_num)
                for blog_post in data:
                    title = blog_post['title']
                    post_url = blog_post['url']
                    publish_date = blog_post['publishDate']
                    titles_and_urls.append({
                            'title': title,
                            'url': post_url,
                            'date':publish_date
                        })
                page_num += 1
        else:
            print(f"Failed to retrieve data from page {page_num} with status code {response.status_code}")
            break
    except:
        print("An unexpected error has ocurred. Check the url on the browser to see if anything has changed.", url)
        break

titles_and_urls = list(set(titles_and_urls))
