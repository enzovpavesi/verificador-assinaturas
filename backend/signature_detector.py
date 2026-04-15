import cv2
import numpy as np
import fitz
from PIL import Image

GOVBR_KEYWORDS = [
    "gov.br", "icp-brasil", "assinatura digital",
    "assinado digitalmente", "certificado digital", "iti", "validar.iti"
]

def load_as_image(file_path: str, ext: str):
    if ext == ".pdf":
        doc = fitz.open(file_path)
        page = doc[0]
        pix = page.get_pixmap(dpi=150)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8)
        img = img_array.reshape(pix.height, pix.width, pix.n)
        doc.close()
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR) if pix.n == 3 else cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    else:
        return cv2.imread(file_path)

def detect_signature(file_path: str, ext: str) -> dict:
    image = load_as_image(file_path, ext)
    if image is None:
        return {"found": False, "region": None}

    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []
    for contour in contours:
        x, y, cw, ch = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)

        # Filtra por características de assinatura:
        # área razoável, não muito grande, na metade inferior do documento
        if (area > 500 and
            cw > 50 and ch > 10 and
            cw < w * 0.8 and ch < h * 0.3 and
            y > h * 0.5):
            candidates.append((x, y, cw, ch, area))

    if candidates:
        largest = max(candidates, key=lambda c: c[4])
        x, y, cw, ch, _ = largest
        return {
            "found": True,
            "region": {"x": x, "y": y, "width": cw, "height": ch}
        }

    return {"found": False, "region": None}

def is_govbr_signature(extracted_text: str, urls: list) -> bool:
    text_lower = extracted_text.lower()

    # Verifica keywords no texto
    if any(kw in text_lower for kw in GOVBR_KEYWORDS):
        return True

    # Verifica se alguma URL aponta para gov.br
    if any("gov.br" in url.lower() or "iti" in url.lower() for url in urls):
        return True

    return False

def has_digital_signature(file_path: str, ext: str) -> bool:
    """Verifica se o PDF tem assinatura digital embutida."""
    if ext != ".pdf":
        return False
    try:
        doc = fitz.open(file_path)
        for page in doc:
            for widget in page.widgets():
                if widget.field_type_string == "Signature":
                    doc.close()
                    return True
        doc.close()
    except Exception:
        pass
    return False