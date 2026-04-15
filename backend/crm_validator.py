import requests

def validate_crm_api(crm_number: str, chave: str) -> dict:
    url = "https://www.consultacrm.com.br/api/index.php"

    params = {
        "tipo": "crm",
        "q": crm_number,
        "chave": chave,
        "destino": "json"
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "true" or data.get("total", 0) == 0:
            return {"status": "INVÁLIDO", "mensagem": "CRM não encontrado.", "dados": None}

        medico = data["item"][0]
        situacao = medico.get("situacao", "").lower()

        if "ativo" in situacao:
            return {
                "status": "VÁLIDO",
                "mensagem": f"CRM ativo. Médico: {medico.get('nome')} — {medico.get('uf')}",
                "dados": medico
            }
        else:
            return {
                "status": "INVÁLIDO",
                "mensagem": f"CRM com situação: {medico.get('situacao')}.",
                "dados": medico
            }

    except requests.exceptions.RequestException as e:
        return {"status": "ERRO", "mensagem": f"Falha ao consultar API: {str(e)}", "dados": None}