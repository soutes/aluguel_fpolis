import scrapy
import re
import math
import json
import os
import smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# carrega credenciais
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
EMAIL_REMETENTE = os.getenv('EMAIL_REMETENTE')
EMAIL_DESTINO   = os.getenv('EMAIL_DESTINO')
EMAIL_PASSWORD  = os.getenv('EMAIL_PASSWORD')

EXISTING_JSON = "imoveis.json"  # ajuste se necessário

def enviar_email(titulo, url):
    msg = MIMEMultipart()
    msg['Subject'] = "Novo Imóvel Cadastrado"
    msg['From']    = EMAIL_REMETENTE
    msg['To']      = EMAIL_DESTINO

    html = f"""
    <p><strong>{titulo}</strong></p>
    <p>Link: <a href="{url}">{url}</a></p>
    """
    msg.add_header('Content-Type', 'text/html')
    msg.attach(MIMEText(html, 'html'))

    try:
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(EMAIL_REMETENTE, EMAIL_PASSWORD)
        s.sendmail(EMAIL_REMETENTE, [EMAIL_DESTINO], msg.as_string())
        s.quit()
        print(f"E-mail enviado para novo imóvel: {titulo}")
    except Exception as e:
        print(f"Erro ao enviar e-mail para {titulo}: {e}")

class IbagyAjaxSpider(scrapy.Spider):
    name = "ibagy_com_email"
    allowed_domains = ["ibagy.com.br"]
    start_urls = ["https://ibagy.com.br/aluguel/residencial/"]
    custom_settings = {'DOWNLOAD_DELAY': 0.6}

    def open_spider(self, spider):
        # carrega códigos já existentes
        self.existing_codes = set()
        if os.path.exists(EXISTING_JSON):
            with open(EXISTING_JSON, encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    for item in data:
                        self.existing_codes.add(str(item.get('codigo')))
                except json.JSONDecodeError:
                    pass
        self.new_items = []

    def close_spider(self, spider):
        # anexa novos itens ao JSON existente
        if self.new_items:
            # carrega tudo (se existir)
            all_items = []
            if os.path.exists(EXISTING_JSON):
                with open(EXISTING_JSON, encoding='utf-8') as f:
                    try:
                        all_items = json.load(f)
                    except:
                        all_items = []
            # adiciona só os new_items (já foram filtrados)
            all_items.extend(self.new_items)
            # salva de volta
            with open(EXISTING_JSON, 'w', encoding='utf-8') as f:
                json.dump(all_items, f, ensure_ascii=False, indent=2)

            # envia e-mail para cada novo
            for item in self.new_items:
                enviar_email(item['titulo'], item['link'])
        else:
            self.logger.info("Nenhum imóvel novo encontrado.")

    def parse(self, response):
        # extrai total de imóveis
        total_text = response.css("p.result-totals-phrase::text").get()
        total = None
        if total_text:
            m = re.search(r"(\d+)", total_text)
            if m: total = int(m.group(1))
        if total is None:
            self.logger.error("Não foi possível extrair o número total de imóveis.")
            return
        self.logger.info(f"Total de imóveis: {total}")

        # pagina inicial
        for imovel in response.css("div.imovel-box-single"):
            item = self.extract_imovel(imovel, response)
            yield item

        # AJAX
        per_page = 12
        if total > per_page:
            pages = math.ceil(total / per_page)
            for p in range(2, pages+1):
                offset = (p-1)*per_page
                url = f"https://ibagy.com.br/u-sr.php?queryData=&reload=0&offset={offset}"
                yield scrapy.Request(url, callback=self.parse_ajax, meta={'offset': offset})

    def parse_ajax(self, response):
        offset = response.meta['offset']
        self.logger.info(f"Processando AJAX offset={offset}")
        for imovel in response.css("div.imovel-box-single"):
            yield self.extract_imovel(imovel, response)

    def extract_imovel(self, imovel, response):
        # código do imóvel
        codigo = imovel.attrib.get('data-codigo','').strip()

        # só processa se for novo
        if codigo in self.existing_codes:
            return  # pula

        titulo = imovel.css('h2.titulo-grid::text').get(default='').strip()
        tipo   = titulo.split()[0] if titulo else ''

        endereco_completo = imovel.css('h3[itemprop="streetAddress"]::text')\
            .get(default='').strip()

        # bairro
        bairro = ""
        if endereco_completo:
            if ',' in endereco_completo:
                partes = endereco_completo.split(',')
                if len(partes) >= 3:
                    bairro = partes[2].split(" - ")[0].strip()
            elif " - " in endereco_completo:
                bairro = endereco_completo.split(" - ")[0].strip()
       
        link_rel = imovel.css("a::attr(href)").get(default='').strip()
        link     = response.urljoin(link_rel)

        preco     = imovel.xpath(".//span[contains(text(),'Valor Total Aprox.:')]/b/text()")\
                        .get(default='').strip()
        quartos   = imovel.css('i.fa-bed + span::text').get(default='').strip()
        vagas     = imovel.css('i.fa-car + span::text').get(default='').strip()
        area_total= imovel.css('i.fa-compress-arrows-alt + span::text')\
                        .get(default='').strip()

        item = {
            'codigo': codigo,
            'titulo': titulo,
            'tipo': tipo,
            'endereco': endereco_completo,
            'bairro': bairro,
            'link': link,
            'preco': preco,
            'quartos': quartos,
            'vagas': vagas,
            'area_total': area_total
        }

        # marca como novo
        self.new_items.append(item)
        # adiciona ao existing para não duplicar na mesma execução
        self.existing_codes.add(codigo)

        return item
