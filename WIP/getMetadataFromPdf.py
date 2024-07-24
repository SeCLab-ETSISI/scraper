from pypdf import PdfReader
from pdftitle import get_title_from_file

def get_metadata(file_path):
    """
    Gets metadata from a given PDF file.

    :param file_path: Path + filename of the PDF file from which metadata is to be extracted.
    :return: A dictionary with all metadata extracted.
    """
    reader = PdfReader(file_path)
    meta = reader.metadata

    print("Number of pages:", len(reader.pages))

    metadata_dict = {
        "Title": meta.title,
        "Author": meta.author,
        "Subject": meta.subject,
        "Creator": meta.creator,
        "Producer": meta.producer,
        "Creation Date": meta.creation_date,
        "Modification Date": meta.modification_date,
        "XMP Metadata": meta.xmp_metadata
    }

    return metadata_dict

def get_title_from_pdf(file_path):
    """
    Gets the title from a given PDF file.

    :param file_path: Path + filename of the PDF file from which the title is to be extracted.
    :return: The title obtained.
    """
    title = get_title_from_pdf_aux(file_path)
    if not title:
        return PdfReader(file_path).metadata.title
    else:
        return title

def get_title_from_pdf_aux(file_path):
    """
    Auxiliary method for get_title_from_pdf.

    :param file_path: Path + filename of the PDF file from which the title is to be extracted.
    :return: The title obtained.
    """
    title = get_title_from_file(file_path)
    print("Title:", title)
    return title
