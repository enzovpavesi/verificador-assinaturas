VALID_KEYWORDS = [
    "válido", "valido", "autêntico", "autentico", "ativo",
    "regular", "verificado", "confirmado", "assinatura válida"
]

INVALID_KEYWORDS = [
    "inválido", "invalido", "cancelado", "revogado", "expirado",
    "irregular", "suspenso", "inativo", "não encontrado"
]

def analyze_result(page_text: str) -> dict:
    text_lower = page_text.lower()

    invalid_score = sum(1 for kw in INVALID_KEYWORDS if kw in text_lower)
    valid_score = sum(1 for kw in VALID_KEYWORDS if kw in text_lower)

    if invalid_score > 0:
        return {
            "status": "INVÁLIDO",
            "mensagem": f"Documento inválido ou assinatura não reconhecida."
        }
    elif valid_score > 0:
        return {
            "status": "VÁLIDO",
            "mensagem": "Assinatura autenticada com sucesso."
        }
    else:
        return{
            "status": "INCONCLUSIVO",
            "mensagem": "Não foi possível determinar a validade. Verifique manualmente."
        }
    
