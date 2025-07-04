# coleta/settings.py

BOT_NAME = "coleta"
SPIDER_MODULES   = ["coleta.spiders"]
NEWSPIDER_MODULE = "coleta.spiders"
ROBOTSTXT_OBEY   = True
DOWNLOAD_DELAY   = 0.6

ITEM_PIPELINES = {
    "coleta.pipelines.ImoveisDedupAndNotifyPipeline": 300,
}

FEEDS = {
    "novos_imoveis.json": {
        "format"   : "json",
        "encoding" : "utf-8",
        "overwrite": True,
        "indent"   : 2,
    }
}
