from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil, os, uuid
from dotenv import load_dotenv

from document_processor import process_document
from rpa_validator import validate_url, validate_govbr
from decision_agent import analyze_result
from crm_validator import validate_crm_api
from signature_detector import detect_signature, is_govbr_signature, has_digital_signature

load_dotenv()
CRM_API_CHAVE = os.getenv("CRM_API_CHAVE")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

@app.post("/validate")
async def validate_document(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Formato não suportado. Use PDF, JPG ou PNG.")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        extracted = process_document(file_path, ext)

        resultado = {
            "urls_encontradas": extracted["urls"],
            "crms_encontrados": [c["crm"] for c in extracted["crms"]],
            "validacao_url": None,
            "validacao_crm": None,
            "validacao_govbr": None
        }

        # Valida URL se encontrou
        if extracted["urls"]:
            url = extracted["urls"][0]
            rpa_result = await validate_url(url)
            decision = analyze_result(rpa_result["page_text"])
            resultado["validacao_url"] = {
                "status": decision["status"],
                "mensagem": decision["mensagem"],
                "url_validada": url,
                "screenshot": rpa_result["screenshot_base64"],
                "texto_pagina": rpa_result["page_text"][:500]
            }

        # Valida CRM se encontrou
        if extracted["crms"]:
            crm_info = extracted["crms"][0]
            crm_result = validate_crm_api(crm_info["crm"], CRM_API_CHAVE)
            resultado["validacao_crm"] = {
                "crm": crm_info["crm"],
                "status": crm_result["status"],
                "mensagem": crm_result["mensagem"],
                "dados": crm_result["dados"]
            }

        if not extracted["urls"] and not extracted["crms"]:

            # Verifica assinatura digital embutida (Gov.br, ICP-Brasil)
            if has_digital_signature(file_path, ext):
                rpa_result = await validate_govbr(file_path)
                decision = analyze_result(rpa_result["page_text"])
                resultado["validacao_govbr"] = {
                    "status": decision["status"],
                    "mensagem": decision["mensagem"],
                    "screenshot": rpa_result["screenshot_base64"]
                }

            else:
                # Tenta detectar assinatura manuscrita com OpenCV
                sig = detect_signature(file_path, ext)

                if not sig["found"]:
                    return {
                        **resultado,
                        "status_geral": "INVÁLIDO",
                        "mensagem": "Nenhuma assinatura, CRM ou QR code encontrado."
                    }

                resultado["validacao_govbr"] = {
                    "status": "NÃO SUPORTADO",
                    "mensagem": "Assinatura manuscrita detectada, mas o tipo não é suportado."
                }

        # Deriva status_geral a partir dos resultados de validação
        all_statuses = [
            resultado[key]["status"]
            for key in ["validacao_url", "validacao_crm", "validacao_govbr"]
            if resultado.get(key) and "status" in resultado[key]
        ]
        if any(s == "INVÁLIDO" for s in all_statuses):
            resultado["status_geral"] = "INVÁLIDO"
        elif any(s == "VÁLIDO" for s in all_statuses):
            resultado["status_geral"] = "VÁLIDO"
        elif all_statuses:
            resultado["status_geral"] = all_statuses[0]
        else:
            resultado["status_geral"] = "INCONCLUSIVO"

        return resultado

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/validate-crm")
def validate_crm_endpoint(crm_number: str):
    result = validate_crm_api(crm_number, CRM_API_CHAVE)
    return {"crm": crm_number, **result}