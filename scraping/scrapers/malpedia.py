import requests
from bs4 import BeautifulSoup
import pandas as pd

country_mapping = {
    "ru": "Russia", "cn": "China", "ir": "Iran", "kp": "North Korea", "tr": "Turkey", "kr": "South Korea",
    "in": "India", "pk": "Pakistan", "il": "Israel", "us": "United States", "lb": "Lebanon", "sy": "Syria",
    "ng": "Nigeria", "by": "Belarus", "fr": "France", "br": "Brazil", "iq": "Iraq", "ke": "Kenya", "es": "Spain",
    "vi": "Vietnam", "tn": "Tunisia", "at": "Austria", "my": "Malaysia", "ro": "Romania", "ps": "Palestine",
    "id": "Indonesia", "ka": "Kazakhstan"
}

def extract_actor_links(url_actor):
    try:
        response = requests.get(url_actor)
        response.raise_for_status()
    except requests.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return []
    except Exception as err:
        print(f"An error occurred: {err}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.find_all('tr', class_='clickable-row clickable-row-newtab')
    links = [row['data-href'] for row in rows]
    return links

def fetch_actors_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return []
    except Exception as err:
        print(f"An error occurred: {err}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.find_all('tr', class_='clickable-row')
    
    actors_info = []

    for row in rows:
        common_name = row.find('td', class_='common_name').get_text(strip=True)
        synonyms = row.find('td', class_='synonyms').get_text(strip=True) if row.find('td', class_='synonyms') else ""
        
        country_span = row.find('td', class_='country').find('span')
        country_code = country_span['title'] if country_span else "Unknown"
        country_name = country_mapping.get(country_code, "Unknown")
        if "Stealth Mango and Tangelo" in common_name:
            common_name = "_stealth_mango_and_tangelo_"
        url_actor = f"https://malpedia.caad.fkie.fraunhofer.de/actor/{common_name.replace(' ', '_').replace('/', '_').lower()}"
        links = extract_actor_links(url_actor)

        actors_info.append({
            "common_name": common_name,
            "country": country_name,
            "links": links,
            "synonyms": synonyms
        })

    return actors_info

url = "https://malpedia.caad.fkie.fraunhofer.de/actors"
actors_info = fetch_actors_data(url)

if not actors_info:
    print("No actor data found.")
else: 
    actors_df = pd.DataFrame(actors_info)
    links_list = []
    for _, row in actors_df.iterrows():
        for link in row['links']:
            website = link.split('/')[2]
            if website[0:3]!="www":
                website = "www." + website
            links_list.append({"actor": row['common_name'], "link": link, "website": website})

    links_df = pd.DataFrame(links_list)

urls = links_df["link"]