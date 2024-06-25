def superScraper(file1):
   url_Button = set()
  with open("URLButton.txt",'r') as b:
    
  with open(file1,'r') as f:
    for line in f:
      if "https://github.com/" in line:
        #call GithubScraper
        print("")
      else: 
        if line in url_Button:
          #call load_more_button.py
          file_Name = line[line.find("www.")+4:line.rfind(".")]
          file_Name = file_Name.replace(".", "")+ ".txt"
          aux = line.split(" ")
          boton(aux[0],aux[1],file_Name)
          #Call function to clear links
          #Llamador(file_Name[:-4], file_Name)
        else:
          #Scraper2(url,url_validas)

          #Or

          #Scraper(url,file_Name)
          #url_validas(file_Name)
          #To call url_validas(file_Name)-> Llamador(file_Name[:-4], file_Name)

          print("")
