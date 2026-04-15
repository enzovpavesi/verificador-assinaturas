import asyncio, subprocess, json, sys, os

RUNNER = os.path.join(os.path.dirname(__file__), "playwright_runner.py")

def _run(mode: str, arg: str) -> dict:
    result = subprocess.run(
        [sys.executable, RUNNER, mode, arg],
        capture_output=True,
        text=True,
        timeout=60
    )
    if result.returncode != 0 or not result.stdout.strip():
        return {"screenshot_base64": None, "page_text": f"Erro: {result.stderr}", "url": arg}
    return json.loads(result.stdout)

async def validate_url(url: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run, "url", url)

async def validate_crm(crm_number: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run, "crm", crm_number)

async def validate_govbr(file_path: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run, "govbr", file_path)