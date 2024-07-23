from bs4 import BeautifulSoup
import urllib.request

# Import the undetected_chromedriver and time libraries
import undetected_chromedriver as uc
import time
import random

import re

from generic_Scraper import  scraperGenerico2
from get_all_links_from_url import remove_duplicates 
from load_more_button import boton

def superScraper(file1):
  url_Button = set()
  #Tratar paginas con load more button
  with open("URLButton.txt",'r') as b:
    for line in b :
      url_Button.add(line)

  with open(file1,'r') as f:
    for line in f:
      x = re.search("^(https?:\/\/)?(www\.)?([^\.]+)?([^\/]+)?", line)
      #x = re.search("^(https?:\/\/)?(www\.)?([^\.]+)?", line)
      if "https://github.com/" in line:
        #call GithubScraper
        print("")
      else:
        fileNameAux = x.group(3) + "Aux" + ".txt"
        fileNameOG = x.group(3) + ".txt"
        urlValida = getattr(UrlValidas, "urlValida" + x.group(3))
        if line in url_Button:
          #call load_more_button.py

          aux = line.split(" ")
          boton(aux[0],aux[1],urlValida)

          parse_url("linksNuevosSeen.txt",x.group())

          remove_duplicates("linksNuevosSeen.txt",fileNameAux)

        else:

          getAllReportLinks(line,urlValida)
          parse_url(fileNameAux,x.group())
        new_lines = check_duplicates(fileNameAux,fileNameOG)

        if len(new_lines) > 0 :
            #Add new lines to FileNameOG
            with open(fileNameOG,'a') as f:
              for line in new_lines:
                f.write(line)
                #f.write("\n")
            #Scrape new lines to BBDD
            scraperGenerico2(new_lines)



def parse_url(input_file,domain_name):
  with open("parseUrlAux.txt",'w') as r:
    with open(input_file,'r') as f:
      for line in f:
        if not line.startswith("http"):
          line2 = domain_name + "/" + line
          r.write(line2)
        else:
          r.write(line)

  with open("parseUrlAux.txt",'r') as r:
    with open(input_file,'w') as f:
      for line in r:
        f.write(line)



def check_duplicates(input_file, output_file):
  newLinks = 0
  lines_seen = set()
  new_lines = set()

  if not os.path.isfile(output_file):
    with open(input_file, 'r') as out_file:
      for line in out_file:
        new_lines.add(line)
    return new_lines

  with open(output_file, 'r') as out_file:
    for line in out_file:
      lines_seen.add(line)

  remove_duplicates(input_file,"checkDuplicatesAux.txt")

  with open("checkDuplicatesAux.txt", 'r') as in_file:
	  for line in in_file:
		  if line not in lines_seen:
				  new_lines.add(line)

  return new_lines



class UrlValidas(object):

    def urlValidaclearskysec(url) :
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

    def urlValidafortinet(url) :
      return True
