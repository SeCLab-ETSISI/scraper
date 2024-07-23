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



# Import the undetected_chromedriver and time libraries
import undetected_chromedriver as uc
import time
from time  import sleep
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def boton(url,button_name, urlVal):

          """
    scrap links from the given URL with a load more button.
 
    :param url: URL of the page with a load more button.
    :param button_name: name of the button class for the url.
    :param urlVal: name of a fuction that returns True if an url contains a report

    """

  # Set ChromeOptions for the headless browser and maximize the window
  options = uc.ChromeOptions()
  options.add_argument("--headless")
  options.add_argument("--start-maximized")

  # Create a new Chrome driver instance with the specified options

  driver = uc.Chrome(options=options)
  # Navigate to the website URL
  #driver.get(url)

  # Wait for the page to load for 10 seconds
  #time.sleep(10)
  #Download images


  driver.get(url)
  #driver.find_element_by_id('bt_gerar_cpf').click()


  #driver.find_element(By.CLASS_NAME, "content")
  #driver.find_element(By.TAG_NAME, "button").click()
  time.sleep(10)

  #loadingButton = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.XPATH,"//div[@id='load_button']")))

  lines_seen = set()
  try:
    os.remove("linksNuevosSeen.txt")
  except OSError:
    pass

  #while( WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn")))):
   #WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn"))).click()
  WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn"))).click()
  html_source = driver.page_source


  while linksNuevos3(html_source,lines_seen, urlVal):
  #while linksNuevos(html_source):
    try:
        # WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@class='btn btn-primary btn-lg']//span[@class='glyphicon glyphicon-play']"))).click()
        WebDriverWait(driver, 300).until(EC.element_to_be_clickable((By.CLASS_NAME, button_name))).click()
        sleep(20)
        html_source = driver.page_source
        print("LOAD MORE RESULTS button clicked")
    except TimeoutException:
        print("No more LOAD MORE RESULTS button to be clicked")
        break

  driver.quit()


import os
from time import sleep

def linksNuevos3(html_body, lines_seen,urlVal):

      """
         Given an html body checks if a new valid url has been found
 
    :param html_body: body of a webpage
    :param lines_seen: urls already seen 
    :param urlVal: name of a fuction that returns True if an url contains a report

      returns True if a new url has been found
    """
      
  #lines_seen = set()
  lines_aux = set()
  result = False
  soup = BeautifulSoup(html_body, "html.parser")
  #print(soup)
  for link in soup.findAll('a'):
      if link.get('href'):
         if link.get('href') not in lines_aux:
          lines_aux.add(link.get('href'))


  for line in lines_aux:
    if line not in lines_seen:
      lines_seen.add(line)
      with open("linksNuevosSeen.txt",'a') as f:
        if urlVal(line):
            f.write(line)
            f.write("\n")
      result = True


#Comprueba para cada linea de linksUtiles si estan ya en todos Los Links, de ser el caso no hace nada, en caso contrario la añade y cambia result a true

  return result
