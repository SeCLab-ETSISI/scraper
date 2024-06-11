import requests
import json
from bs4 import BeautifulSoup

def extract_all_reports():
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
    return titles_and_urls

def parse_complex_table(table):
    rows = []
    for row in table.find_all('tr'):
        cells = row.find_all('td')
        for cell in cells:
            rows.append(cell.get_text(separator="\n"))
    return rows

def scrape_blog_content(url):
    response = requests.get(url)
    previous_info_table_text = "Empty"
    incrusted_table = False
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.find('div', class_='col-md-9 col-lg-9 col-sm-12')  # Adjust the class as needed
        
        if content:
            # Extract tables and their preceding headers
            tables = []
            for table in content.find_all('table'):
                info_table_tag = table.find_previous_sibling(['p','h3'])
                info_table_text = info_table_tag.get_text() if info_table_tag else "Empty"
                if info_table_text == "\u00a0":
                    info_table_text = previous_info_table_text
                elif len(info_table_text) > 200:
                    info_table_text = "Incrusted table on the text"
                    incrusted_table = True
                # Extract table headers and rows
                table_data = []
                headers = [header.get_text() for header in table.find_all('tr')[0].find_all('td')]
                
                for row in table.find_all('tr'):
                    cells = row.find_all('td')
                    row_data = {cells[i].get_text() for i in range(len(cells))}
                    table_data.append(row_data)
                if len(table_data) == 0:
                    table_data = parse_complex_table(table)
                tables.append({'info_table': info_table_text, 'data': table_data})

                table.extract()
                if info_table_tag:
                    if not incrusted_table:
                        info_table_tag.extract()

                    if info_table_tag.get_text() != "\u00a0":
                        previous_info_table_text = info_table_text
                incrusted_table = False
            
            text_content = content.get_text(separator="\n") if content else "Content not found"
        
        else:
            text_content, tables = "Content not found", []
        
        return text_content, tables
    else:
        return "Failed to retrieve content", []

titles_and_urls = list(set(extract_all_reports()))

for entry in titles_and_urls:
    content, tables = scrape_blog_content(entry['url'])
    entry['content'] = content
    entry['tables'] = tables
    print(content)
    print()
    for i in tables:
        print(i)
    break
