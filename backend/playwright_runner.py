import asyncio
import sys, json, base64

# Configura ProactorEventLoop antes de qualquer coisa
asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.sync_api import sync_playwright

def validate_url(url: str) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            page.goto(url, timeout=30000, wait_until="networkidle")
            page.wait_for_timeout(2000)
            screenshot_base64 = base64.b64encode(page.screenshot(full_page=True)).decode("utf-8")
            page_text = page.inner_text("body")
            return {"screenshot_base64": screenshot_base64, "page_text": page_text, "url": url}
        except Exception as e:
            return {"screenshot_base64": None, "page_text": f"Erro: {str(e)}", "url": url}
        finally:
            browser.close()

def validate_crm(crm_number: str) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            page.goto("https://portal.cfm.org.br/busca-medicos", timeout=30000, wait_until="networkidle")
            page.fill('input#crm', crm_number)
            page.click('button.btn-buscar')
            page.wait_for_timeout(3000)
            screenshot_base64 = base64.b64encode(page.screenshot(full_page=True)).decode("utf-8")
            page_text = page.inner_text("body")
            return {"crm": crm_number, "screenshot_base64": screenshot_base64, "page_text": page_text}
        except Exception as e:
            return {"crm": crm_number, "screenshot_base64": None, "page_text": f"Erro: {str(e)}"}
        finally:
            browser.close()

def validate_govbr(file_path: str) -> dict:
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            page.goto("https://validar.iti.gov.br", timeout=30000, wait_until="networkidle")

            # Upload direto no input oculto
            page.set_input_files('input#signature_files', file_path)
            page.wait_for_timeout(2000)

            # Clica em Validar
            page.get_by_text("Validar").click()
            page.wait_for_timeout(5000)

            screenshot_base64 = base64.b64encode(page.screenshot(full_page=True)).decode("utf-8")
            page_text = page.inner_text("body")

            return {
                "screenshot_base64": screenshot_base64,
                "page_text": page_text
            }
        except Exception as e:
            return {"screenshot_base64": None, "page_text": f"Erro: {str(e)}"}
        finally:
            browser.close()

if __name__ == "__main__":
      mode = sys.argv[1]
      arg  = sys.argv[2]

      if mode == "url":
          result = validate_url(arg)
      elif mode == "crm":
          result = validate_crm(arg)
      elif mode == "govbr":
          result = validate_govbr(arg)
      else:
          result = {"error": "Modo inválido"}

      print(json.dumps(result))