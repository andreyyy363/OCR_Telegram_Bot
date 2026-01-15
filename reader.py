import os
import zipfile
import fitz
import docx
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'


# For local run on Windows, uncomment and set the correct path to tesseract.exe
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def recognize_text_from_image(image_path, lang='eng'):
    """
    Function to extract text from an image using Tesseract OCR

    :param image_path: - path to the image file
    :param lang: - language for OCR
    :return: text: - extracted text
    """
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image, lang=lang)
    return text


def recognize_text_from_pdf(pdf_path, lang='eng'):
    """
    Function to extract text from a PDF file using PyMuPDF and Tesseract OCR

    :param pdf_path: - path to the PDF file
    :param lang: - language for OCR
    :return: text: - extracted text
    """

    doc = fitz.open(pdf_path)
    text = ''
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_path = f"temp_image_{page_num}_{xref}.png"
            with open(image_path, "wb") as img_file:
                img_file.write(image_bytes)
            text += recognize_text_from_image(image_path, lang)
            os.remove(image_path)
    return text


def recognize_text_from_docx(docx_path, lang='eng'):
    """
    Function to extract text from a DOCX file using python-docx and Tesseract OCR

    :param docx_path: - path to the DOCX file
    :param lang: - language for OCR
    :return: text: - extracted text
    """
    doc = docx.Document(docx_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"

    temp_dir = os.path.join(os.path.dirname(docx_path), 'temp_docx_images')
    image_paths = extract_images_from_docx(docx_path, temp_dir)
    for image_path in image_paths:
        try:
            text += recognize_text_from_image(image_path, lang) + "\n"
        except Exception as e:
            text += f"\n[Error processing image {os.path.basename(image_path)}: {e}]\n"
        finally:
            os.remove(image_path)

    os.rmdir(temp_dir)
    return text


def extract_images_from_docx(docx_path, extract_dir):
    """
    Extract images from a DOCX file to a specified directory.

    :param docx_path: path to the DOCX file
    :param extract_dir: directory where images will be extracted
    :return: list of extracted image file paths
    """
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)

    image_paths = []

    with zipfile.ZipFile(docx_path) as z:
        for file in z.namelist():
            if file.startswith('word/media/'):
                filename = os.path.basename(file)
                output_file = os.path.join(extract_dir, filename)

                with open(output_file, 'wb') as f:
                    f.write(z.read(file))

                image_paths.append(output_file)

    return image_paths


def process_input_files(file_paths, lang):
    """
    Function to process files and extract text based on the file type

    :param file_paths: - list of file paths
    :param lang: - lang choice
    :return: results: - dictionary with file names and extracted text
    """

    results = {}
    for file_path in file_paths:
        if file_path.endswith('.pdf'):
            text = recognize_text_from_pdf(file_path, lang)
        elif file_path.endswith('.docx') or file_path.endswith('.doc'):
            text = recognize_text_from_docx(file_path, lang)
        elif file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
            text = recognize_text_from_image(file_path, lang)
        else:
            text = "Unsupported file format"

        results[os.path.basename(file_path)] = text

    return results


def save_texts_to_files(texts, output_dir):
    """
    Function to save extracted texts to files

    :param texts: - dictionary with file names and extracted text
    :param output_dir: - directory to save the output files
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename, text in texts.items():
        output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.txt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
