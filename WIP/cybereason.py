url = "https://www.cybereason.com/blog/category/research"

def remove_duplicates(input_file, output_file):
	lines_seen = set()
	with open(output_file, 'w') as out_file:
		with open(input_file, 'r') as in_file:
			for line in in_file:
				if line not in lines_seen:
					out_file.write(line)
					lines_seen.add(line)
          

def AñadirURLalTXTCybereason(url):
  html_page = urllib.request.urlopen(url)
  soup = BeautifulSoup(html_page, "html.parser")
  with open('output.txt', 'a') as f:
    for link in soup.findAll('a'):
      if link.get('href'):
        f.write(link.get('href'))
        f.write("\n")

def remove_cybereason(input_file, output_file):
  with open(output_file, 'w') as out_file:
    with open(input_file, 'r') as in_file:
      for line in in_file:
        if "https://www.cybereason.com/blog/"  in line:
          if "https://www.cybereason.com/blog/all" not in line:
            out_file.write(line)


AñadirURLalTXTCybereason(url)

remove_duplicates("output.txt", "outputR.txt")
remove_cybereason("outputR.txt", "outputC.txt")

#Queda borrar output.txt y outputR.txt
