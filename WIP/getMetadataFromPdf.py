#!pip install pypdf
#!pip install pdftitle

from pypdf import PdfReader
from pdftitle import  get_title_from_file


def getMetadata(file1):

      """
    Gets metadata from a given pdf file
 
    :param file1: path + filename of the pdf file from which metadata is to be extracted

    returns a dict with all metadata extracted
    """
  
  reader = PdfReader(file1)
  meta = reader.metadata
 
  print("Number of pages : ",len(reader.pages))

  # All of the following could be None!
  
  dict = {"Title":meta.title,"Author":meta.author,"Subject":meta.subject,"Creator":meta.creator,"Producer":meta.producer,"Creation Date":meta.creation_date,"Modification Date":meta.modification_date}
  dict["XMP Metadata"] = meta.xmp_metadata

  return dict

def getTitleFromPdf(filePath1):

      """
    Gets Title from a given pdf file
 
    :param filePath1: path + filename of the pdf file from which metadata is to be extracted

    returns a the title obtained
    """
  
  if(getTitleFromPdfAux(filePath1) == ""):
    # returns the title specified in the metadata
    return PdfReader(filePath1).metadata.title
  else:
    # returns the title obtained
    return getTitleFromPdfAux(filePath1)


def getTitleFromPdfAux(filePath1):

      """
    Auxiliar method for getTitleFromPdf
 
    :param filePath1: path + filename of the pdf file from which metadata is to be extracted

    returns the title obtained
    """
  
  title = get_title_from_file(filePath1)
  print("Title:", title)
  return title

