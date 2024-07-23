from generic_Scraper import byPassScrapper

from bs4 import BeautifulSoup
import urllib.request

# Import the undetected_chromedriver and time libraries
import undetected_chromedriver as uc
import time
import random


def obtenerLinksUtiles2(html_source,urlVal):

      """
    get useful links from a html source of a webpage
 
    :param html_source: source code of an html web page
    :param urlVal: name of a function that returns true if a url contains a report 
      
    returns the number of useful links found
    """
  
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
  #remove_duplicates("linksUtiles.txt","enlacesUnicos.txt")
  return i



def remove_duplicates(input_file, output_file):

      """
    removes duplicates from file
 
    :param input_file: File from which duplicates are to be removed
    :param output_file: File where the result will be saved 
      
    returns a dict with all the urls seen
    """
  
	newLinks = 0
	lines_seen = set()
	with open(output_file, 'w') as out_file:
		with open(input_file, 'r') as in_file:
			for line in in_file:
				if line not in lines_seen:
					out_file.write(line)
					lines_seen.add(line)
					newLinks = newLinks + 1
	return newLinks



import random
import os
#scrapper principal llama al auxiliar al recorrer el bucle

def getAllReportLinks(url,urlVal):

      """
    Given an url return all report links find in said webpage
 
    :param url: url from where reports are to be extracted
    :param urlVal: name of a function that returns true if a url contains a report 
      
    returns a dict with all the urls seen
    """
  
  n = random.randrange(3,17)
  pagina = 1

  x = re.search("^(https?:\/\/)?(www\.)?([^\.]+)?", url)

  FileName = x.group(3) + "Aux"+ ".txt"

  try:
    os.remove(FileName)
  except OSError:
    pass


  nuevaUrl = url + "page/" + str(pagina)
  #nuevaUrl hace referencia al metodo de paginación que usa la pagina objetivo, podría ser interesante pasarla como parametro a la función en caso de que se detecten webs con nomenclaturas diferentes.

  
  html_source = byPassScrapper(url)

  try:
    os.remove("linksUtiles.txt")
  except OSError:
    pass


  while(obtenerLinksUtiles2(html_source,urlVal)>0):
    #Añadir comprobación de que el http code sea 200 Ok en caso de ser necesario
    
    pagina = pagina + 1
    nuevaUrl = url + "page/" + str(pagina)

    html_source = byPassScrapper(nuevaUrl)
    
    
  
  index = remove_duplicates("linksUtiles.txt",FileName)
  
