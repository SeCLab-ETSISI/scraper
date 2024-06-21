#!pip install trafilatura
#!pip install selenium undetected-chromedriver
#!wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && apt install ./google-chrome-stable_current_amd64.deb

from bs4 import BeautifulSoup
import urllib.request

# Import the undetected_chromedriver and time libraries
import undetected_chromedriver as uc
import time
import random

import hashlib
def getHashFromString(str):
  return hashlib.sha256(str.encode('utf-8')).hexdigest()

def remove_duplicates(input_file, output_file):
	lines_seen = set()
	with open(output_file, 'w') as out_file:
		with open(input_file, 'r') as in_file:
			for line in in_file:
				if line not in lines_seen:
					out_file.write(line)
					lines_seen.add(line)

def buscarPDF(html_source):
  encontrado = False
  soup = BeautifulSoup(html_source, "html.parser")
  for link in soup.findAll('a'):
    if link.get('href'):
      if link.get('href').endswith(".pdf"):
        #descargarPDF
        encontrado = True
        print("encontrado:" +link.get('href'))
        with open("encontrado.txt",'a') as enc:
          enc.write(link.get('href'))
          enc.write("\n")
  return encontrado


def obtenerLinksUtiles2(html_source,urlVal):
  i = 0

  soup = BeautifulSoup(html_source, "html.parser")

  with open("linksUtiles.txt","a") as l:

    for link in soup.findAll('a'):
      #if link.get('href'):
        if urlVal(link.get('href')):
          #guardar todos los links en un fichero auxiliar
          l.write(link.get('href'))
          l.write("\n")
          i = i + 1
  remove_duplicates("linksUtiles.txt","enlacesUnicos.txt")
  return i


def byPassScrapper(url):


  # Set ChromeOptions for the headless browser and maximize the window
  options = uc.ChromeOptions()
  options.add_argument("--headless")
  options.add_argument("--start-maximized")

  # Create a new Chrome driver instance with the specified options

  driver = uc.Chrome(options=options)
  print(url)
  # Navigate to the website URL
  driver.get(url)

  # Wait for the page to load for 10 seconds
  time.sleep(10)


  #obtener html de la pagina web
  html_source = driver.page_source

  with open("aux.txt",'w') as aux:
    aux.write(html_source)

  # Quit the browser instance
  driver.quit()

  return html_source


def ScrapperAux2(nuevaUrl,urlVal):
  n = random.randrange(3,17)

  html_source = byPassScrapper(nuevaUrl)

  obtenerLinksUtiles2(html_source,urlVal)

  with open("enlacesUnicos.txt","r") as l:
    for line in l:
      sleep(n)
      #print(1)
      #print(line)
      html_pdf = byPassScrapper(line)
      #print (html_pdf)
      if(not buscarPDF(html_pdf)):
        extraccionTextoEImagenes2(html_pdf,"/content/prueba4/")

  return html_source

import random
import os
#scrapper principal llama al auxiliar al recorrer el buble

def Scrapper2(url,urlVal):
  n = random.randrange(3,17)
  pagina = 1
  #url = "https://www.clearskysec.com/category/threat-actors/"
  nuevaUrl = url + "page/" + str(pagina)
  #nuevaUrl hace referencia al metodo de paginación que usa la pagina objetivo, podría ser interesante pasarla como parametro a la función en caso de que se detecten webs con nomenclaturas diferentes.

  #html_source = ScrapperAux2(url,urlVal)
  html_source = byPassScrapper(url)

  try:
    os.remove("linksUtiles.txt")
  except OSError:
    pass


  while(obtenerLinksUtiles2(html_source,urlVal)>0):
    #Añadir comprobación de que el http code sea 200 Ok
    print(pagina)
    pagina = pagina + 1
    nuevaUrl = url + "page/" + str(pagina)
    html_source = ScrapperAux2(nuevaUrl,urlVal)
    try:
      os.remove("linksUtiles.txt")
    except OSError:
      pass


from trafilatura import extract
from trafilatura import fetch_url
from trafilatura.readability_lxml import is_probably_readerable
import os

from lxml.html.soupparser import convert_tree

def extraccionTextoEImagenes2 (html,path):

    try:

      is_probably_readerable(html)

      texto = extract(html)

      #obtener Titulo del articulo para crear carpeta
      Titulo = getHashFromString(texto)

      print(Titulo)

      newpath = path +  Titulo + "/"

      if not os.path.exists(newpath):
        n = os.makedirs(newpath)
      #Guardamos el texto en un archivo txt cuyo nombre es el hash sha256 del texto que se pretende guardar
      #tituloTexto = newpath  + "/" + Titulo + ".txt"
      tituloTexto = newpath  + Titulo + ".txt"


      with open(tituloTexto, 'w') as f:
        f.write(texto)

      #Procedemos a descargar las imagenes usando la función descargar imagenes
      descargarImagenesDeURL2(newpath,html,newpath)
    except:
      print("ERROR 200: url has no readable text")



import requests
import random
from time import sleep

def descargarImagenesDeURL2(newpath, response, path):
  #Buscar todos los links a archivos png

  html = extract(response, include_images=True)

  candidatos = html.split()

  for candidato in candidatos:
    if candidato.startswith("![](http") and (candidato.endswith(".png)")or candidato.endswith(".jpg)") or candidato.endswith(".jpeg)")):
      try:
        urlImagen = candidato[4:-1]
        n = random.randrange(3,17)
        sleep(n)
        descargarImagen2(newpath,urlImagen,path)
      except:
        print("Error 300: Image could not be downloaded from url : " + candidato)


  #para cada link llamar a la funcion descargarImagen



# Import the undetected_chromedriver and time libraries
import undetected_chromedriver as uc
import time
import random

def descargarImagen2(newpath, imagen_url,path):
  # Set ChromeOptions for the headless browser and maximize the window
  options = uc.ChromeOptions()
  options.add_argument("--headless")
  options.add_argument("--start-maximized")

  # Create a new Chrome driver instance with the specified options

  driver = uc.Chrome(options=options)
  # Navigate to the website URL
  #driver.get(url)

  # Wait for the page to load for 10 seconds
  time.sleep(10)
  #Download images


  nombre = path + "//" +imagen_url[imagen_url.rfind("/"):]
  #nombre = path + getHashFromString(imagen_url) + ".png"
  print(nombre)
  nombre2 = nombre[:nombre.rfind(".")] + ".png"
  print(nombre2)
  driver.get(imagen_url)
  driver.save_screenshot(nombre2)
  # Quit the browser instance
  driver.quit()





def urlValidaClearskysec(url) :
  if url.count('/') == 4 :
      if url.count('/company/') < 1 :
        if url.count('https://www.clearskysec.com/solutions/') < 1 :
          if url.count('https://www.clearskysec.com/blog/') < 1 :
            if url.count('https://www.clearskysec.com/partners/') < 1 :
              if url.count('https://www.clearskysec.com/contact-us/') < 1 :
                if url.count('https://www.clearskysec.com/feed/') < 1 :
                  return True
  else:
    return False

def urlValidaMalwarebytes(url) :
  if url.count('/') == 7 :
      if url.startswith("https://www.malwarebytes.com/blog/threat-intelligence/") :
        return True
  else:
    return False


def urlValidaTalosintelligence(url):
  if url.count('/') == 4:
    if url.startswith("https://blog.talosintelligence.com/"):
      return True
  else:
    return False    
