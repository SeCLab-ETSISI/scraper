# Import the undetected_chromedriver and time libraries
import undetected_chromedriver as uc
import time
from time  import sleep
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

#receives an

def boton(url,button_name,file1):

      """
    scrap links from the given URL with a load more button.
 
    :param url: URL of the page with a load more button.
    :param button_name: name of the button class for the url.
    :param file1: file in which the scraped URLs will be saved.

    returns file1
    """
  
  # Set ChromeOptions for the headless browser and maximize the window
  options = uc.ChromeOptions()
  options.add_argument("--headless")
  options.add_argument("--start-maximized")

  # Create a new Chrome driver instance with the specified options

  driver = uc.Chrome(options=options)


  driver.get(url)

  time.sleep(10)

  lines_seen = set()

  WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn"))).click()
  html_source = driver.page_source


  while linksNuevos3(html_source,lines_seen,file1):
  #while linksNuevos(html_source):
    try:
        WebDriverWait(driver, 300).until(EC.element_to_be_clickable((By.CLASS_NAME, button_name))).click()
        sleep(20)
        html_source = driver.page_source
        print("LOAD MORE RESULTS button clicked")
    except TimeoutException:
        print("No more LOAD MORE RESULTS button to be clicked")
        break

  driver.quit()

  return file1




import os
from time import sleep

def linksNuevos3(html_body, lines_seen,file1):

      """
    Auxiliar method for boton().
 
    :html_body: html_body of a webpage.
    :lines_seen: set with the url already seen.
    :param file1: file in which the scraped URLs will be saved.

    returns file1
    """
  
  #lines_seen = set()
  lines_aux = set()
  result = False
  soup = BeautifulSoup(html_body, "html.parser")
  #finds all href in the html body and adds it to a set
  for link in soup.findAll('a'):
      if link.get('href'):
         if link.get('href') not in lines_aux:
          lines_aux.add(link.get('href'))

  #checks if the urls are new, in case they are result = true and the links are added to the txt
  for line in lines_aux:
    if line not in lines_seen:
      lines_seen.add(line)
      with open(file1,'a') as f:
            f.write(line)
            f.write("\n")
      result = True

  return result
