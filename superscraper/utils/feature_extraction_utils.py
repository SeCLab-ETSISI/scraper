import oletools.oleid
import oletools.rtfobj
import oletools.mraptor
from oletools import rtfobj
from oletools.olevba import VBA_Parser, TYPE_OLE, TYPE_OpenXML, TYPE_Word2003_XML, TYPE_MHTML
import json
import os

import pickle
import pandas as pd
import die, pathlib
import numpy as np
import subprocess

import r2pipe

import datetime 

import multiprocessing

import hashlib

import random

from dataframe_utils import insert_dict_to_mongo

from globals import HEADERS, MONGO_CONNECTION_STRING, MONGO_DATABASE, MONGO_COLLECTION, SCRAPING_TIME, PATH_TO_IOCSEARCHER , EXE_FEATURE_COLLECTION , DOC_FEATURE_COLLECTION


def get_hashes_from_file(filename):


    """
    For a specific file returns its md5, sha1 and sha256 hashes .
    
    Parameters:
    - file_path: Path of the file to be hashed. 
    
    Returns:
    - md5: md5 hash from the input file.
    - sha1: sha1 hash from the input file.
    - sha256: sha256 hash from the input file.

    """    

    BUF_SIZE = 65536
    md5 = hashlib.md5()
    sha1 =hashlib.sha1()
    sha256 = hashlib.sha256()


    with open(filename, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
            sha1.update(data)
            sha256.update(data)

    return md5.hexdigest() , sha1.hexdigest() , sha256.hexdigest()

def get_oleid_df(filename):
    """
    For a specific file generates a dict with the results from oleid scan.
    
    Parameters:
    - file_path: Path of the file to be analyzed by avclass. 
    
    Returns:
    - indicators_json: Formated dict with the results from oleid scan.
    """
    oid = oletools.oleid.OleID(filename)
    indicators = oid.check()
    indicators_json = {}
    for i in indicators:
        indicators_json[i.name] =  i.value
 
    return indicators_json


def get_rtfobj_df(filepath):

    """
    For a specific file generates a dict with the results from rtfobj scan.
    
    Parameters:
    - file_path: Path of the file to be analyzed by avclass. 
    
    Returns:
    - rtfobjJson: Formated dict with the results from rtfobj scan.
    """
    rtfobj_json = { }
    aux2 = ""
    i = 0
    for index, orig_len, data in rtfobj.rtf_iter_objects(filepath):
        aux = ""
        aux = aux + "size : " + str(len(data)) + " , "
        aux = aux + "index : " + str(index) + " , "
        field_name = "Object : " + str(i)
        aux2 = aux2 + field_name + " : " + aux + " | "
        i += 1
    rtfobj_json['rtf_obj'] = aux2  

    return rtfobj_json

def get_olevba_with_mraptor_df(filepath):

  """
    For a specific file generates a dict with the results from olevba and Mraptor scans.
    
    Parameters:
    - file_path: Path of the file to be analyzed by avclass. 
    
    Returns:
    - olevba_json: Formated dict with the results from olevba and Mraptor scans.
    """
    
  olevba_json = { }
  aux2 = ""
  i = 0
  with open(filepath, 'rb') as f:
    filedata = f.read()
  vbaparser = VBA_Parser(filepath, data=filedata,)  
  olevba_json["tipo"] = vbaparser.type
  if vbaparser.detect_vba_macros():
    olevba_json["VBA Macros"] = "VBA Macros found"
    for (filename, stream_path, vba_filename, vba_code) in vbaparser.extract_macros():
      #aux ={}
      aux = ""
      aux = aux + "filename : " + filename + " , "
      aux = aux + "stream_path : " + stream_path + " , "
      aux = aux + "vba_filename : " + vba_filename + " , "
      aux = aux + "vba_code : " + vba_code + " , "


      raptor = oletools.mraptor.MacroRaptor(vba_code)
      raptor.scan()
      aux = aux + "Mraptor_suspicious" + str(raptor.suspicious) + " , "
      aux = aux + "Mraptor_autoexec_flag" + str(raptor.autoexec) + " , "
      aux = aux + "Mraptor_write_flag" + str(raptor.write) + " , "
      aux = aux + "Mraptor_execute_flag" + str(raptor.execute) + " , "

      
      field_name = "VBA Macros Info " + str(i)
      aux2 = aux2 + field_name + " : "  + aux + " | "
      i += 1
    olevba_json["VBA Macros Info"] = aux2
  else:
    olevba_json["VBA Macros"] = "No VBA Macros found"  
    olevba_json["VBA Macros Info"] = "No VBA Macros found"

  results = vbaparser.analyze_macros(show_decoded_strings=True)
  aux2 = ""
  i = 0
  if results is not None:  
      for kw_type, keyword, description in results:
        aux =""
        aux = aux + "kw_type : " + kw_type + " , "
        aux = aux + "keyword : " + keyword  + " , "
        aux = aux + "description" + description  + " , "
        field_name = "VBA Macros analysis " + str(i)
        aux2 = aux2 + field_name + " : "  + aux + " | "
        i += 1
      olevba_json["VBA Macros analysis"] = aux2 
      #print(json.dumps(olevba_json, indent=4)) 
  return olevba_json

def get_row_for_document_df(filepath):
    
    """
    For a specific file generates a row with the features Extracted.
    
    Parameters:
    - file_path: Path of the file to be analyzed by avclass. 
    
    Returns:
    - oleidDf: Formated row to append to the dataFrame.
    """
    
    oleid_df = get_oleid_df(filepath)
    rtfobj_df = get_rtfobj_df(filepath)
    olevba_df = get_olevba_with_mraptor_df(filepath)

    oleid_df.update(rtfobj_df)
    oleid_df.update(olevba_df)
    
    return oleid_df

    import sys



def prepare_file_for_radare(filename):
  """
    creates a pipe to use radare on a file .
    
    Parameters:
    - filename: Path to the file. 
    
    Returns:
    - r2pipe.open(filename): pipe for radare

    """ 
  return r2pipe.open(filename)

def get_import_table_as_json(r):
  json_out = r.cmdj('iij')
  return json_out

def get_file_info_as_json(r):
  json_out = r.cmdj('iIj')
  return json_out

def get_linked_libraries_as_json(r):
  json_out = r.cmdj('ilj')
  return json_out

def get_imports_as_json(r):
  json_out = r.cmdj('iij')
  return json_out

def get_entry_point_as_json(r):
  json_out = r.cmdj('iej')
  return json_out

def get_sections_data_as_json(r):
  json_out = r.cmdj('iSj')
  return json_out

def get_simbols_as_json(r):
  json_out = r.cmdj('isj')
  return json_out

def get_all_exports_from_file(r,filename):
  json_out = r.cmdj(f'rabin2 -j -E "{filename}"')
    
  return json_out

def get_general_information_as_json(r):
  json_out = r.cmd('ij')
  return json_out

def get_entropy_from_file_sections(r,filename):
  json_out = r.cmdj(f'rabin2 -K entropy -S -j "{filename}"')  
  return json_out

def check_for_no_executable_stack(r):
  if "true" in r.cmd('i~nx'):
    return True
  else:
    return False

def check_for_position_independent_code(r):
  if "true" in r.cmd('i~pic'):
    return True
  else:
    return False

def check_for_canary(r):
  if "true" in r.cmd('i~canary'):
    return True
  else:
    return False

def get_iocs_from_file(filename, path_to_iocsearcher= "iocsearcher" ):  
  destination = json_to_txt(filename)  
  shell_comand = path_to_iocsearcher + " -f " + destination
  subprocess.run(shell_comand, shell=True, check=True)
    
  if os.path.exists(destination):
        os.remove(destination)
  return destination + ".iocs"

def json_to_txt(filename):
  now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
  random_int = random.randint(1, 1000000) 
  destination = "./feature_extraction/aux/auxForIoCs"+ str(now) + str(random_int) +".txt"
  
  with open(filename,'r') as data:
    with open(destination, 'w') as f:
      f.write(data.read()) 
  return destination 

def iocs_as_array(filepath):

  with open(filepath, 'r') as f:
    aux = ""  
    for line in f:
        tipo, contenido = line.split("	")
        partes = contenido.rsplit("\n", 1)
        contenido = ''.join(partes)
        aux = aux + tipo + " : " + contenido + " | " 
        
  return aux


def expand_feature_name_for_df(dicta,expansion):
    resul = {}
    for key in dicta:
        new_key = expansion + "." + str(key)
        resul[new_key] = dicta[key]
    return [resul]  


    
def add_entry_point_to_df(dicta):
    resul = {}
    for key in dicta:
        new_key = "entryPoint." + str(key)
        resul[new_key] = dicta[key]
    return [resul]  

def transform_data_to_string_for_df_generic(Lista):
    aux = ""
    for element in Lista:
        aux = aux + str(element) + " , "
    return aux 

def transform_data_to_string_for_df_entropy(dicta):
    aux = ""
    try:
        for element in dicta["sections"]:
            aux = aux + str(element) + " , "
    except:
        return transform_data_to_string_for_df_generic(dicta)
    return aux 

def get_strings_from_file_sections(r,filename):
  json_out = r.cmdj(f'rabin2 -K entropy -izz -j "{filename}"')  
  return json_out

def obtain_all_data_from_file_as_rows_f(filename):
    #Check if the file is an executable
            
            r = prepare_file_for_radare(filename)
            
            #Obtains the imports table from the file
            import_table_json = get_import_table_as_json(r)
            import_table_for_df = transform_data_to_string_for_df_generic(import_table_json)

            
            #Obtains the exports table from the file
            export_table_json = get_all_exports_from_file(r,filename)
            export_table_for_df = transform_data_to_string_for_df_generic(export_table_json)

            #Obtains the entropy from the sections of the file        
            entropy_from_file_section = get_entropy_from_file_sections(r,filename)
            entropy_from_file_section_for_df = transform_data_to_string_for_df_entropy(entropy_from_file_section)
            
            section_data = get_sections_data_as_json(r)
            section_data_for_df = transform_data_to_string_for_df_generic(section_data)
            
            
            simbols = get_simbols_as_json(r)
            simbols_for_df = transform_data_to_string_for_df_generic(simbols)

            
            
            entry_point = get_entry_point_as_json(r)
            entry_point_for_df = expand_feature_name_for_df(entry_point[0] ,"entry_point")

            
            
            file_info = get_file_info_as_json(r)

            

            md5 , sha1 , sha256 = get_hashes_from_file(filename)

            

            file_info["md5"] =  md5
            file_info["sha1"] = sha1
            file_info["sha256"] = sha256

            
        
            strings = get_strings_from_file_sections(r,filename)

            
            try:
                #strings_for_df = transform_data_to_string_for_df_string(strings['strings'])
                strings_for_df = strings['strings']
            except:
                strings_for_df = ""
                
            
            r.quit()

            #use Floss to obtain all strings 
            
            file_info.update(entry_point_for_df[0])

           
            
            file_info["import_table"] =  import_table_for_df
            file_info["export_table"] = export_table_for_df
            file_info["section_data"] = section_data_for_df
            file_info["simbols"] = simbols_for_df
            file_info["strings"] = strings_for_df

            
            
            try:

                now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                random_int = random.randint(1, 1000000) 
                destination_strings_floss =  "./feature_extraction/aux/malware_strings" + str(now) + str(random_int) +".json" 
                with open (destination_strings_floss,'w') as f:
                    json.dump(strings_for_df, f, indent=4) 
                
                # Use IoCSearcher to get IoCs

                #GetIoCsFromFile(filename)

                # Comienzo de la seccion critica? 
                
                iocs_destination = get_iocs_from_file(destination_strings_floss, PATH_TO_IOCSEARCHER)
                
                file_info["IoCs"] = iocs_as_array(iocs_destination)
                 
                try:
                    if os.path.exists(destination_strings_floss):
                        os.remove(destination_strings_floss)
                except:
                    pass


                try:
                    if os.path.exists(iocs_destination):
                        os.remove(iocs_destination)
                except:
                    pass
                
            except:

                file_info["IoCs"] = "IoCs Could not be extracted"
                
                try:
                    if os.path.exists(destination_strings_floss):
                        os.remove(destination_strings_floss)
                except:
                    pass
            
                
            return file_info
     
def update_pickle(exec_features_pickle , doc_features_pickle , unsupported_files_pickle):
  try: 
      with open("./feature_extraction/pickle/exec_features_pickle.pk", "rb") as f:   # Unpickling 
        exec_features_pickle_o = pickle.load(f)
      exec_features_pickle_o += exec_features_pickle
      with open("./feature_extraction/pickle/exec_features_pickle.pk", "wb") as f:
        pickle.dump(exec_features_pickle_o, f)
  except:
     with open("./feature_extraction/pickle/exec_features_pickle.pk", "wb") as f:
        pickle.dump(exec_features_pickle, f)

  try:  
      with open("./feature_extraction/pickle/doc_features_pickle.pk", "rb") as f:   # Unpickling 
        doc_features_pickle_o = pickle.load(f)
      doc_features_pickle_o += doc_features_pickle
      with open("./feature_extraction/pickle/doc_features_pickle.pk", "wb") as f:
        pickle.dump(doc_features_pickle_o, f)    
  except:
     with open("./feature_extraction/pickle/doc_features_pickle.pk", "wb") as f:
        pickle.dump(doc_features_pickle, f)

  try:  
      with open("./feature_extraction/pickle/unsupported_files_pickle.pk", "rb") as f:   # Unpickling 
        unsupported_files_pickle_o = pickle.load(f)
      unsupported_files_pickle_o += unsupported_files_pickle
      with open("./feature_extraction/pickle/unsupported_files_pickle.pk", "wb") as f:
        pickle.dump(unsupported_files_pickle_o, f)    
  except:
      with open("./feature_extraction/pickle/unsupported_files_pickle.pk", "wb") as f:
        pickle.dump(unsupported_files_pickle, f)

def filter_df_by_time(df):

    filtered_df = df[df["time"] >= SCRAPING_TIME]
    return filtered_df

def get_features_from_a_file(filepath,magika,sha256):
    #Get filetipe from the file in question 
    feature_extraction_method = get_feature_extraction_method(magika)
    if feature_extraction_method == "Executable":
    #Get Row for exec file
        exec_row = obtain_all_data_from_file_as_rows_f(filepath)
        return exec_row , "features_from_executable_files"        
        
    elif feature_extraction_method == "features_from_documents":
        #Get Row for Doc
        doc_row = get_row_for_document_df(filepath)
        return doc_row , "features_from_document_files"

    else: 
        with open("./feature_extraction/Logs/UnsupportedFilesLog.txt", 'a') as f:
            #cont = "Error unsupported File Type  : " + str(row['file_path']) + "\n"
            cont = "Error unsupported File Type  : " + str(filepath) + "\n"
            f.write(cont)
        return sha256 , "unsupported"

def get_feature_extraction_method(magika_file_type):
    executable_files = ['pebin','elf','mach-o']
    documents_files = ['doc','xls','pub','vsd','docx','xlsx', 'pptx','docm','xlsm', 'pptm','mht','mhtml','rtf']
    if magika_file_type in executable_files:
        return "Executable" 
    elif magika_file_type in documents_files:
        return "features_from_documents"    
    else:
        return "unsupported"

def chunk_data(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        #yield data[i:i + chunk_size]
        df = pd.DataFrame(data[i:i + chunk_size])
        yield df

def get_features_from_dataframe_for_chunks(df , logs_lock):
    exec_rows = [] 
    # load from database execDf 
      
    doc_rows = [] 
    #Load from database docDf


    unsupported_files_pickle = []
    #Load unsupportedFileType from Db it has to be deleted from db when a new filetype is supported
    for index, row in df.iterrows():
        try:
      
                filepath = row['file_path']


            
                row_features, file_type = get_features_from_a_file(filepath,str(row['file_type_magika']),row['sha256'])

                  
                
                if file_type == "unsupported":
                  unsupported_files_pickle += [row_features]
                else:
                  #Guardar en la base de datos y actualizar el pickle que corresponda. 
                  #push_element_to_database(row, file_type, row['sha256'])
                  if file_type == "features_from_executable_files":
                    exec_rows.append(row_features) 
                      
                  elif file_type == "features_from_document_files":
                    doc_rows.append(row_features)  
                    
                        
        except Exception as e :
            with logs_lock:
                with open("./feature_extraction/Logs/ErrorLog.txt",'a') as f:
                    f.write("Error extracting features from file : " + str(filepath) + " Detailed Info :" + str(e) + '\n')

    return exec_rows , doc_rows , unsupported_files_pickle
    #return exec_df_new , doc_df_new , unsupported_file_type_hash

def get_features_from_dataframe_for_chunks_wrap(df,db_lock , logs_lock):
    
        
    exec_rows , doc_rows , unsupported_file_type_hash = get_features_from_dataframe_for_chunks(df ,  logs_lock )

    with db_lock:
        #update_database
        update_mongo(exec_rows , doc_rows)
        #Write_to_pickle
        update_pickle(exec_rows , doc_rows , unsupported_file_type_hash)


def update_mongo(exec_rows , doc_rows):
   
   for element in exec_rows:
      try:
        insert_with_retry(element,EXE_FEATURE_COLLECTION)
      except:
        pass
   for element in doc_rows:
      try:
         insert_with_retry(element,DOC_FEATURE_COLLECTION)
      except:
         pass       



def insert_with_retry(element, collection, retries=2):
    for attempt in range(1, retries + 1):
        try:
            insert_dict_to_mongo(element, collection)
            return  # Exit if successful
        except Exception as e:
            if attempt == retries:
              with open("./feature_extraction/Logs/mongo_error_log.txt",'a') as f:
                f.write(f"Failed to insert element into {collection} after {retries} attempts: {e}")

def create_needed_dir():
   
   os.makedirs("./feature_extraction/aux/", exist_ok=True)
   os.makedirs("./feature_extraction/Logs/", exist_ok=True)
   os.makedirs("./feature_extraction/pickle/", exist_ok=True)

def get_features(df):
    create_needed_dir()
    with multiprocessing.Manager() as manager:
        # Create shared locks
        lock_db = manager.Lock()
        lock_log = manager.Lock()


        #df = filter_df(df)
        df = filter_df_by_time(df)

        num_processes = max(1, os.cpu_count() // 2)
        rows = df.to_dict(orient="records")
        chunk_size = max(1, len(rows) // (2 * num_processes))  # Dynamic chunk size
        with multiprocessing.Pool(processes=num_processes) as pool:
            pool.starmap(get_features_from_dataframe_for_chunks_wrap, [(chunk, lock_db, lock_log ) for chunk in chunk_data(rows, chunk_size)])
