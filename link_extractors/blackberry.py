import requests
import json

def fetch_blackberry_links(page_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json'
    }

    try:
        response = requests.get(page_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        links = []

        for item in data:
            for category in item.get('category', []):
                if 'Research & Intelligence' in category.get('name', ''):
                    link = item.get('url')
                    if link:
                        links.append(link)
                    break
        return links
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return []

def extract_all_reports():
    page_num = 1
    all_links = []
    
    while True:
        url = f"https://blogs.blackberry.com/bin/blogs?page={page_num}&category=https://blogs.blackberry.com/en/category/research-and-intelligence&locale=en"
        response = requests.get(url)
        try:
            if response.status_code == 200:
                data = json.loads(response.text)
                if len(data) == 0:
                    break
                else:
                    print(f"[+] Processing page {page_num}")
                    for blog_post in data:
                        post_url = blog_post['url']
                        all_links.append(post_url)
                    page_num += 1
            else:
                print(f"[-] Failed to retrieve data from page {page_num} with status code {response.status_code}")
                break
        except Exception as e:
            print(f"[-] An unexpected error has occurred. Check the URL in the browser to see if anything has changed. {url}")
            print(str(e))
            break
    
    return all_links

if __name__ == "__main__":
    links = extract_all_reports()
    print(f"Found {len(links)} BlackBerry URLs.")
