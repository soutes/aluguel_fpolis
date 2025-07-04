# coleta/utils/email_utils.py

import smtplib
import os
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Carrega .env na raiz do projeto
env_path = Path(__file__).parents[2] / ".env"
load_dotenv(env_path)

EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
EMAIL_PASSWORD  = os.getenv("EMAIL_PASSWORD")
EMAIL_DESTINO   = os.getenv("EMAIL_DESTINO")


def enviar_email_resumo(novos_itens):
    """
    Envia um ÚNICO email listando todos os imóveis novos.
    novos_itens: lista de dicts com 'titulo' e 'link'.
    """
    msg = MIMEMultipart()
    msg["Subject"] = "Resumo: Novos Imóveis Cadastrados"
    msg["From"]    = EMAIL_REMETENTE
    msg["To"]      = EMAIL_DESTINO

    html = "<h2>Foram cadastrados novos imóveis:</h2><ul>"
    for itm in novos_itens:
        titulo = itm.get("titulo","").replace("&","&amp;")
        link   = itm.get("link","#")
        html  += f"<li><a href='{link}' target='_blank'>{titulo}</a></li>"
    html += "</ul>"

    msg.add_header("Content-Type","text/html")
    msg.attach(MIMEText(html,"html"))

    with smtplib.SMTP("smtp.gmail.com",587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_REMETENTE, EMAIL_PASSWORD)
        smtp.sendmail(EMAIL_REMETENTE, [EMAIL_DESTINO], msg.as_string())

    print(f"[email] Resumo enviado com {len(novos_itens)} imóveis.")
