#requirements
#!pip install trafilatura
#!pip install selenium undetected-chromedriver
#!wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && apt install ./google-chrome-stable_current_amd64.deb



# Import the undetected_chromedriver and time libraries
import undetected_chromedriver as uc
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import urllib.request

def boton(url):
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
  

  #while( WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn")))):
   #WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn"))).click()
  WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn"))).click()
  html_source = driver.page_source
  

  while linksNuevos(html_source):
    try:
        # WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@class='btn btn-primary btn-lg']//span[@class='glyphicon glyphicon-play']"))).click()
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn"))).click()
        html_source = driver.page_source
        print("LOAD MORE RESULTS button clicked")
    except TimeoutException:
        print("No more LOAD MORE RESULTS button to be clicked")
        break

  #driver.find_element(By.CLASS_NAME, "nRhiJb-LgbsSe  nRhiJb-LgbsSe-OWXEXe-CNusmb-o6Shpd ")
  
  #driver.find_element(By.CLASS_NAME, "btn").click() 

  #while(driver.find_element(By.CLASS_NAME, "btn")):
  #  time.sleep(5)
   # driver.find_element(By.CLASS_NAME, "btn").click()
    #print(driver.find_element(By.CLASS_NAME, "btn"))


  time.sleep(10)

  # Take a screenshot of the page and save it as "screenshot.png"
  #driver.save_screenshot("screenshot.png")

  #obtener html de la pagina web
  html_source = driver.page_source

  with open("aux.txt",'w') as aux:
    aux.write(html_source)


  soup = BeautifulSoup(html_source, "html.parser")
  with open("linksUtiles.txt","a") as l:

    for link in soup.findAll('a'):
      #if link.get('href'):
        #if urlVal(link.get('href')):
          #guardar todos los links en un fichero auxiliar
          l.write(link.get('href'))
          l.write("\n")

 
  driver.quit()



import os
from time import sleep

def linksNuevos(html_body):
  lines_seen = set()
  result = False
  soup = BeautifulSoup(html_body, "html.parser")

#Añade todos los links del html_body a un txt de nombre links utiles
  with open("linksUtiles.txt","w") as l:

    for link in soup.findAll('w'):
      if link.get('href'):
        #if urlVal(link.get('href')):
          #guardar todos los links en un fichero auxiliar
          l.write(link.get('href'))
          l.write("\n")

# Añade todas las lineas de todosLosLinks a lines seen
  with open("todosLosLinks.txt",'a+') as t:
    for line in t:
      lines_seen.add(line)

  contar()

#Comprueba para cada linea de linksUtiles si estan ya en todos Los Links, de ser el caso no hace nada, en caso contrario la añade y cambia result a true  
  with open("todosLosLinks.txt", 'a') as out_file:
    with open("/content/linksUtiles.txt", 'r') as in_file: 
      count = sum(1 for _ in in_file)
      print(count)
      for line in in_file:
        print(line)
        if line not in lines_seen:
          out_file.write(line)
          lines_seen.add(line)
          result = True

  print(result)
  return result



from ctypes import sizeof
import os
from time import sleep

def linksNuevos2(html_body):
  lines_seen = set()
  result = False
  soup = BeautifulSoup(html_body, "html.parser")
  with open("/content/todosLosLinks.txt",'a+') as t:
    for line in t:
      lines_seen.add(line)

    print(len(lines_seen))

  for link in soup.findAll('w'):
    if link.get('href'):
      print(1)

  with open("/content/todosLosLinks.txt",'a') as t:  
    for link in soup.findAll('w'):
      if link.get('href'):
        #if urlVal(link.get('href')):
          #guardar todos los links en un fichero auxiliar
          if link.get('href') not in lines_seen:
            t.write(link.get('href'))
            lines_seen.add(link.get('href'))
            result = True
    print(len(lines_seen))        
  return result  

def contar():
    with open("linksUtiles.txt", 'a+') as f:
      f.seek(0)
      coun = sum(1 for _ in f)
      print(coun)




