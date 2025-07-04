import scrapy
import re
import math

class IbagyAjaxSpider(scrapy.Spider):
    name = "daltonandrade_ajax"  # Valor original; retiraremos o sufixo "_ajax" para a imobiliária.
    allowed_domains = ["daltonandrade.com.br"]
    start_urls = ["https://daltonandrade.com.br/aluguel/residencial/"]

    custom_settings = {
        'DOWNLOAD_DELAY': 0.6,
    }

    def parse(self, response):
        # Extrai o total de imóveis (por exemplo: "1011 imóveis encontrados")
        total_text = response.css("p.result-totals-phrase::text").get()
        total = None
        if total_text:
            total_match = re.search(r"(\d+)", total_text)
            if total_match:
                total = int(total_match.group(1))
        if total is None:
            self.logger.error("Não foi possível extrair o número total de imóveis.")
            return
        self.logger.info(f"Total de imóveis: {total}")

        # Processa os 12 imóveis carregados na página inicial
        for imovel in response.css("div.imovel-box-single"):
            yield self.extract_imovel(imovel, response)

        results_per_page = 12
        if total > results_per_page:
            num_pages = math.ceil(total / results_per_page)
            self.logger.info(f"Total de páginas: {num_pages}")
            # A partir da segunda página, os blocos são carregados via AJAX
            # Usamos o endpoint https://daltonandrade.com.br/u-sr.php?queryData=&reload=0 com o parâmetro offset
            for page in range(2, num_pages + 1):
                offset = (page - 1) * results_per_page
                ajax_url = f"https://daltonandrade.com.br/u-sr.php?queryData=&reload=0&offset={offset}"
                self.logger.info(f"Requisitando AJAX com offset {offset}: {ajax_url}")
                yield scrapy.Request(ajax_url,
                                     callback=self.parse_ajax,
                                     meta={'offset': offset})

    def parse_ajax(self, response):
        offset = response.meta.get('offset', 0)
        self.logger.info(f"Processando AJAX com offset {offset}")
        imoveis = response.css("div.imovel-box-single")
        if not imoveis:
            self.logger.warning(f"Nenhum imóvel encontrado com offset {offset}.")
        for imovel in imoveis:
            yield self.extract_imovel(imovel, response)

    def extract_imovel(self, imovel, response):
        # Extrai o título do imóvel
        titulo = imovel.css('h2.titulo-grid::text').get(default='').strip()
        # Cria o campo "tipo" com a primeira palavra do título
        tipo = titulo.split()[0] if titulo else ''

        # Extrai o endereço completo a partir de h3 com itemprop "streetAddress"
        endereco_completo = imovel.css('h3[itemprop="streetAddress"]::text').get(default='').strip()

        # Extrai o bairro a partir do endereço
        if endereco_completo:
            if ',' in endereco_completo:
                partes = endereco_completo.split(',')
                if len(partes) >= 3:
                    # Tenta extrair o bairro do terceiro elemento, dividindo por " - "
                    bairro = partes[2].split(" - ")[0].strip()
                else:
                    # Se não houver três partes, tenta usar o split por " - "
                    if " - " in endereco_completo:
                        bairro = endereco_completo.split(" - ")[0].strip()
                    else:
                        bairro = endereco_completo
            elif " - " in endereco_completo:
                # Se não houver vírgula, usa o split por " - "
                bairro = endereco_completo.split(" - ")[0].strip()
            else:
                bairro = endereco_completo
        else:
            bairro = ""


        # Extrai o link do imóvel (assumindo que o container contenha um <a> com o link)
        link_relativo = imovel.css("a::attr(href)").get(default='').strip()
        link = response.urljoin(link_relativo)

        # Extração dos demais campos
        preco = imovel.xpath(".//span[contains(text(), 'Valor Total:')]/b/text()").get(default='').strip()
        quartos = imovel.css('i.fa-bed + span::text').get(default='').strip()
        vagas = imovel.css('i.fa-car + span::text').get(default='').strip()
        area_total = imovel.css('i.fa-compress-arrows-alt + span::text').get(default='').strip()

        return {
            'titulo': titulo,
            'tipo': tipo,
            'endereco': endereco_completo,
            'bairro': bairro,
            'link': link,
            'preco': preco,
            'quartos': quartos,
            'vagas': vagas,
            'area_total': area_total,
            'imobiliaria': self.name.replace("_ajax", "")  # Remove _ajax para deixar somente o nome real da imobiliária.
        }
