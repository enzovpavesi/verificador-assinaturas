import fitz  # PyMuPDF
from PIL import Image
from pyzbar import pyzbar
import cv2, numpy as np, pytesseract, re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

import fitz
from PIL import Image
from pyzbar import pyzbar
import cv2, numpy as np, pytesseract, re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def process_document(file_path: str, ext: str) -> dict:
    if ext == ".pdf":
        urls, crms, texto = extract_from_pdf(file_path)
    else:
        urls, crms, texto = extract_from_image(file_path)

    crms_vistos = set()
    crms_unicos = []
    for c in crms:
        if c["crm"] not in crms_vistos:
            crms_vistos.add(c["crm"])
            crms_unicos.append(c)

    return {
        "urls": list(set(urls)),
        "crms": crms_unicos,
        "texto": texto
    }

def extract_from_pdf(file_path: str) -> tuple:
    urls, crms = [], []
    texto_completo = ""
    doc = fitz.open(file_path)

    for page in doc:
        for link in page.get_links():
            if link.get("uri"):
                urls.append(link["uri"])

        text = page.get_text()
        texto_completo += " " + text
        urls.extend(extract_urls_from_text(text))
        crms.extend(extract_crm_from_text(text))

        for img_info in page.get_images():
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            img_array = np.frombuffer(base_image["image"], np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if img is not None:
                urls.extend(decode_qr_codes(img))

    doc.close()
    return urls, crms, texto_completo.strip()

def extract_from_image(file_path: str) -> tuple:
    urls, crms = [], []

    img = cv2.imread(file_path)
    if img is not None:
        urls.extend(decode_qr_codes(img))

    pil_img = Image.open(file_path)
    text = pytesseract.image_to_string(pil_img, lang='por')
    texto_completo = text
    urls.extend(extract_urls_from_text(text))
    crms.extend(extract_crm_from_text(text))

    return urls, crms, texto_completo.strip()
    
def decode_qr_codes(img) -> list:
    urls = []
    for obj in pyzbar.decode(img):
        data = obj.data.decode("utf-8")
        if data.startswith("http"):
            urls.append(data)
    return urls

def extract_urls_from_text(text: str) -> list:
    pattern = r'https?://[^\s\)\]\>\"\']+'
    return re.findall(pattern, text)

def extract_crm_from_text(text: str) -> list:
    pattern = r'CRM[\/\-\s]?([A-Z]{2})?[\s:\/\-]*(\d[\d\.]{4,})'
    matches = re.findall(pattern, text.upper())
    result = []
    for match in matches:
        uf = match[0]
        num = match[1]
        result.append({"crm": num.replace(".", ""), "uf": uf})
    return result