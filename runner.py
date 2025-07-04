# runner.py

import subprocess
import time
from pathlib import Path

import schedule
from dotenv import load_dotenv

# 1) Carrega as variáveis de ambiente (.env)
load_dotenv(Path(__file__).parent / ".env")

# 2) Defina o diretório raiz do seu projeto (onde está scrapy.cfg)
PROJECT_DIR = Path(__file__).parent

# 3) Comando para chamar o seu spider via Poetry
SCRAPY_CMD = ["poetry", "run", "scrapy", "crawl", "ibagy_com_cod"]

def run_scraper():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Iniciando o scraper...")
    # executa o scrapy no diretório do projeto
    result = subprocess.run(
        SCRAPY_CMD,
        cwd=str(PROJECT_DIR),
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("[✔] Scraper finalizado sem erros")
    else:
        print(f"[✖] Scraper retornou código {result.returncode}")
        print(result.stderr)

if __name__ == "__main__":
    # roda uma vez imediatamente
    run_scraper()

    # agenda para rodar a cada 8 horas
    schedule.every(8).hours.do(run_scraper)

    print("⏰ Agendado para rodar a cada 8 horas. Ctrl+C para sair.")
    while True:
        schedule.run_pending()
        time.sleep(60)
