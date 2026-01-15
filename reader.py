import os
import zipfile
import io
import fitz
import docx
from PIL import Image, UnidentifiedImageError
import pytesseract

# Set the path to the Tesseract executable for Docker environment
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'


# For local run on Windows, uncomment and set the correct path to tesseract.exe
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def recognize_text_from_image(image_path, lang='eng'):
    """
    Function to extract text from an image using Tesseract OCR

    :param image_path: path to the image file or PIL Image object
    :param lang: language for OCR
    :return: text: extracted text
    """
    if isinstance(image_path, str):
        image = Image.open(image_path)
    else:
        image = image_path
    text = pytesseract.image_to_string(image, lang=lang)
    return text


def recognize_text_from_pdf(pdf_path, lang='eng'):
    """
    Function to extract text from a PDF file using PyMuPDF and Tesseract OCR

    :param pdf_path: path to the PDF file
    :param lang: language for OCR
    :return: text: extracted text
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

            try:
                image = Image.open(io.BytesIO(image_bytes))
                text += recognize_text_from_image(image, lang)
            except (OSError, UnidentifiedImageError, pytesseract.pytesseract.TesseractError) as e:
                text += f"\n[Error processing image on page {page_num + 1}: {e}]\n"

    return text


def recognize_text_from_docx(docx_path, lang='eng'):
    """
    Function to extract text from a DOCX file using python-docx and Tesseract OCR

    :param docx_path: path to the DOCX file
    :param lang: language for OCR
    :return: text: extracted text
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
        except (OSError, UnidentifiedImageError, pytesseract.pytesseract.TesseractError) as e:
            text += f"\n[Error processing image {os.path.basename(image_path)}: {e}]\n"
        finally:
            if os.path.exists(image_path):
                os.remove(image_path)

    if os.path.isdir(temp_dir) and not os.listdir(temp_dir):
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

    :param file_paths: list of file paths
    :param lang: Tesseract OCR language code(s), e.g. 'eng' for English, 'fra' for French,
    or 'eng+fra' for multiple languages
    :return: results: dictionary with file names and extracted text
    """

    results = {}
    for file_path in file_paths:
        if file_path.endswith('.pdf'):
            text = recognize_text_from_pdf(file_path, lang)
        elif file_path.endswith('.docx'):
            text = recognize_text_from_docx(file_path, lang)
        elif file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
            text = recognize_text_from_image(file_path, lang)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")

        base_name = os.path.basename(file_path)
        key = base_name

        if key in results:
            name, ext = os.path.splitext(base_name)
            counter = 1

            while True:
                candidate = f"{name}_{counter}{ext}"
                if candidate not in results:
                    key = candidate
                    break
                counter += 1

        results[key] = text

    return results


def save_texts_to_files(texts, output_dir):
    """
    Function to save extracted texts to files

    :param texts: dictionary with file names and extracted text
    :param output_dir: directory to save the output files
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename, text in texts.items():
        output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.txt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)

# # Example usage
# file_path = ['test/text_word_ukr_eng.docx', 'test/1.png']
# alphabet = 'eng'
# output_path = 'outputs'
# text = process_input_files(file_path, alphabet)
# save_texts_to_files(text, output_path)
