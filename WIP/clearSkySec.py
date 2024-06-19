#requeriments
#!pip install trafilatura
#!pip install selenium undetected-chromedriver
#!wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && apt install ./google-chrome-stable_current_amd64.deb




import time
from time import sleep
from trafilatura import extract
from trafilatura import fetch_url
from trafilatura.readability_lxml import is_probably_readerable
import os
from bs4 import BeautifulSoup
import urllib.request

import undetected_chromedriver as uc

import random


# Función que permite remover lineas duplicadas de un fichero
def remove_duplicates(input_file, output_file):
	lines_seen = set()
	with open(output_file, 'w') as out_file:
		with open(input_file, 'r') as in_file:
			for line in in_file:
				if line not in lines_seen:
					out_file.write(line)
					lines_seen.add(line)




#dada un html localiza todas las urls del mismo

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
          #print(link.get('href'))
          i = i + 1
  remove_duplicates("linksUtiles.txt","enlacesUnicos.txt")
  return i




# verifica si la url dada como parametro es valida
def urlValida(url) :
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



#dado un html localiza todos los archivos .pdf y los guarda en un fichero de nombre encontrado.txt
def buscarPDF(html_source):
  soup = BeautifulSoup(html_source, "html.parser")
  for link in soup.findAll('a'):
    if link.get('href'):
      if link.get('href').endswith(".pdf"):
        #descargarPDF
        print("encontrado:" +link.get('href'))
        with open("encontrado.txt",'a') as enc:
          enc.write(link.get('href'))
          enc.write("\n")


#Función auxiliar para el scraper

def clearSkySecScraperAux2(nuevaUrl,urlVal):
  n = random.randrange(3,17)

  html_source = byPassScraper(nuevaUrl)

  obtenerLinksUtiles2(html_source,urlVal)

  with open("enlacesUnicos.txt","r") as l:
    for line in l:
      sleep(n)
      #print(1)
      #print(line)
      html_pdf = byPassScraper(line)
      #print (html_pdf)
      buscarPDF(html_pdf)

  return html_source




#scraper principal llama al auxiliar al recorrer el buble

def clearSkySecScraper2(url,urlVal):
  n = random.randrange(3,17)
  pagina = 1
  #url = "https://www.clearskysec.com/category/threat-actors/"
  nuevaUrl = url + "page/" + str(pagina)

 
  html_source = clearSkySecScraperAux2(url,urlVal)


  
  try:
    os.remove("linksUtiles.txt")
  except OSError:
    pass


  print("hola")
  while(obtenerLinksUtiles2(html_source,urlVal)>0):
    print(pagina)
    pagina = pagina + 1
    nuevaUrl = url + "page/" + str(pagina)
    html_source = clearSkySecScraperAux2(nuevaUrl,urlVal)
    try:
      os.remove("linksUtiles.txt")
    except OSError:
      pass
