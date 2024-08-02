import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

async def extract_links():
    base_url = "https://www.secureworks.com/research?page="
    page_num = 1
    report_links = []

    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")  # Disable GPU acceleration
    options.add_argument("--no-sandbox")  # Bypass OS security model
    options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    while True:
        url = f"{base_url}{page_num}"
        print(f"Fetching URL: {url}")  # Debugging print
        driver.get(url)
        await asyncio.sleep(3)  # Wait for the page to load

        containers = driver.find_elements(By.CLASS_NAME, "cards-container")
        print(f"Cards container found: {len(containers) > 0}")  # Debugging print

        if not containers:
            break

        container = containers[0]
        print(f"Container HTML on page {page_num}:\n{container.get_attribute('innerHTML')[:500]}")  # Debugging print
        
        links = container.find_elements(By.CSS_SELECTOR, "a.FilterCard")
        print(f"Number of links found on page {page_num}: {len(links)}")  # Debugging print
        
        if not links:
            break

        for link in links:
            href = link.get_attribute("href")
            if href:
                print(f"Found link: {href}")  # Debugging print
                report_links.append(href)
        
        page_num += 1

    driver.quit()
    return report_links

extract_links.__name__ = "secureworks_extractor"

if __name__ == "__main__":
    links = asyncio.run(extract_links())
    print(f"Total number of links found: {len(links)}")  # Debugging print
