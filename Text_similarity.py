# requisitos

# !pip install datasketch


from datasketch import MinHash

#from nltk.corpus import stopwords
#import nltk

def getMinHashFromFullText(texto):
  #set_a = [word for word in texto if word not in stopwords.words('english')]
  #Quizas remover las stopwords usando nltk stopwords
  set_a = texto.split()
  mh_a = MinHash()
  for item in set_a:
    mh_a.update(repr(item).encode('utf8'))
  return mh_a

def getSimilarityFromMinHashes(mh_a,mh_b):
  similarity = mh_a.jaccard(mh_b)
  return similarity


