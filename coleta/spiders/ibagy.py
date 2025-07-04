# coleta/spiders/ibagy.py

import scrapy
import re
import math

class IbagyComCodSpider(scrapy.Spider):
    name            = "ibagy_com_cod"
    allowed_domains = ["ibagy.com.br"]
    start_urls      = ["https://ibagy.com.br/aluguel/residencial/"]
    custom_settings = {
        'DOWNLOAD_DELAY': 0.6,
    }

    def parse(self, response):
        total_text = response.css("p.result-totals-phrase::text").get() or ""
        m = re.search(r"(\d+)", total_text)
        total = int(m.group(1)) if m else 0
        self.logger.info(f"Total de imóveis: {total}")

        # primeira página
        for im in response.css("div.imovel-box-single"):
            yield self.extract_imovel(im, response)

        # demais páginas via AJAX
        per_page = 12
        pages   = math.ceil(total / per_page)
        for p in range(2, pages + 1):
            offset = (p-1)*per_page
            url    = f"https://ibagy.com.br/u-sr.php?queryData=&reload=0&offset={offset}"
            yield scrapy.Request(url, callback=self.parse_ajax, meta={'offset': offset})

    def parse_ajax(self, response):
        offset = response.meta['offset']
        self.logger.info(f"AJAX offset={offset}")
        for im in response.css("div.imovel-box-single"):
            yield self.extract_imovel(im, response)

    def extract_imovel(self, im, response):
        codigo = im.css("button.btn-favorito::attr(data-codigo)").get(default="").strip()
        titulo = im.css('h2.titulo-grid::text').get(default='').strip()
        tipo   = titulo.split()[0] if titulo else ''
        endereco = im.css('h3[itemprop="streetAddress"]::text').get(default='').strip()

        # extrai bairro
        bairro = ""
        if endereco:
            if ',' in endereco:
                parts = endereco.split(',')
                if len(parts) >= 3:
                    bairro = parts[2].split(" - ")[0].strip()
            elif " - " in endereco:
                bairro = endereco.split(" - ")[0].strip()

        link_rel = im.css("a::attr(href)").get(default="").strip()
        link     = response.urljoin(link_rel)

        preco      = im.xpath(".//span[contains(text(),'Valor Total Aprox.:')]/b/text()")\
                         .get(default='').strip()
        quartos    = im.css('i.fa-bed + span::text').get(default='').strip()
        vagas      = im.css('i.fa-car + span::text').get(default='').strip()
        area_total = im.css('i.fa-compress-arrows-alt + span::text').get(default='').strip()

        return {
            'codigo'    : codigo,
            'titulo'    : titulo,
            'tipo'      : tipo,
            'endereco'  : endereco,
            'bairro'    : bairro,
            'link'      : link,
            'preco'     : preco,
            'quartos'   : quartos,
            'vagas'     : vagas,
            'area_total': area_total
        }
