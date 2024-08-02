# requisitos

# !pip install datasketch


from datasketch import MinHash

#from nltk.corpus import stopwords
#import nltk

def getMinHashFromFullText(texto):

   """
    Returns the minhash of a given text.

    Parameters:
    text: text from which to get the minhash
    returns mn_a: minhash from text a
    """
  
  #set_a = [word for word in texto if word not in stopwords.words('english')]
  #Quizas remover las stopwords usando nltk stopwords
  set_a = texto.split()
  mh_a = MinHash()
  for item in set_a:
    mh_a.update(repr(item).encode('utf8'))
  return mh_a

def getSimilarityFromMinHashes(mh_a,mh_b):

     """
    Returns similarity between two given hashes.

    Parameters:
    mh_a: minhash from first text
    mh_b: minhash from second text
    returns similarity: number between 0 and 1, closer to 1 means more similar 
    """
  
  similarity = mh_a.jaccard(mh_b)
  return similarity


