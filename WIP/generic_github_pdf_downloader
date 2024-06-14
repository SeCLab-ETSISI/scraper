

def find_nth(haystack: str, needle: str, n: int) -> int:
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start

#AñadirURLalTXTAllGit es una función que guarda en un txt de nombre output.txt todos los links de descarga de archivos pdf de un repositorio de github cuya url recibe como parametro

def AñadirURLalTXTAllGit(url):
  start = find_nth(url,"/",4)
  end = find_nth(url,"/",5)
  repoName = url[start:end]
  html_page = urllib.request.urlopen(url)
  soup = BeautifulSoup(html_page, "html.parser")
  with open('output.txt', 'a') as f:
    for link in soup.findAll('a'):
      if link.get('href'):
        if link.get('href').endswith(".pdf") :
          if repoName in link.get('href'):
            link2 = "https://github.com/" + link.get('href').replace("blob","raw",1)
            f.write(link2)
            f.write("\n")
          else: 
            if "https://github.com/" in link.get('href'):
              f.write(link.get('href').replace("blob","raw",1))
              f.write("\n") 
            else:
              f.write(link.get('href'))
              f.write("\n") 
