# coleta/pipelines.py

import json
from pathlib import Path
from scrapy.exceptions import DropItem
from coleta.utils.email_utils import enviar_email_resumo

class ImoveisDedupAndNotifyPipeline:
    # Encontra o imoveis.json na raiz do projeto (duas pastas acima deste arquivo)
    EXISTING_JSON = Path(__file__).parents[2] / "imoveis.json"

    def __init__(self):
        self.existing_codes = set()
        if self.EXISTING_JSON.exists():
            try:
                data = json.loads(self.EXISTING_JSON.read_text(encoding="utf-8"))
                for itm in data:
                    if "codigo" in itm:
                        self.existing_codes.add(str(itm["codigo"]))
            except Exception:
                pass
        self.new_items = []

    def process_item(self, item, spider):
        codigo = item.get("codigo")
        if not codigo or str(codigo) in self.existing_codes:
            # já existe, descarta
            raise DropItem(f"Duplicado: {codigo}")
        # novo: registra
        self.existing_codes.add(str(codigo))
        self.new_items.append(item)
        return item

    def close_spider(self, spider):
        if not self.new_items:
            spider.logger.info("Nenhum imóvel novo para anexar.")
            return

        # 1) Anexa os novos ao JSON existente
        all_items = []
        if self.EXISTING_JSON.exists():
            try:
                all_items = json.loads(self.EXISTING_JSON.read_text(encoding="utf-8"))
            except Exception:
                all_items = []

        all_items.extend(self.new_items)
        self.EXISTING_JSON.write_text(
            json.dumps(all_items, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        spider.logger.info(f"{len(self.new_items)} novos imóveis adicionados em {self.EXISTING_JSON}")

        # 2) Envia UM email resumo
        enviar_email_resumo(self.new_items)
