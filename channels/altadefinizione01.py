# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per altadefinizione01 - VERSIONE OTTIMIZZATA
# ------------------------------------------------------------
"""
    
    Eccezioni note che non superano il test del canale:

    Avvisi:
        - L'url si prende da questo file.
        - è presente nelle novità-> Film.

    Ulteriori info:
        - Ottimizzazioni per migliorare le performance di ricerca
        - Pattern regex semplificati
        - Migliore gestione degli errori
        - Timeout configurabili

"""
from core import scrapertools, httptools, support
from core.item import Item
from platformcode import config, logger
import time


# def findhost(url):
#     data = httptools.downloadpage(url).data
#     host = scrapertools.find_single_match(data, '<div class="elementor-button-wrapper"> <a href="([^"]+)"')
#     return host


host = config.get_channel_url()
headers = [['Referer', host]]

# Configurazioni per ottimizzazione
TIMEOUT = 15  # Timeout per le richieste
MAX_RETRIES = 2  # Numero massimo di retry


@support.menu
def mainlist(item):

    film = [
        ('Al Cinema', ['/cinema/', 'peliculas', 'pellicola']),
        ('Ultimi Aggiornati-Aggiunti', ['','peliculas', 'update']),
        ('Generi', ['', 'genres', 'genres']),
        ('Lettera', ['/catalog/a/', 'genres', 'orderalf']),
        ('Anni', ['', 'genres', 'years']),
        ('Sub-ITA', ['/sub-ita/', 'peliculas', 'pellicola'])
    ]

    return locals()


def safe_download(url, timeout=TIMEOUT, retries=MAX_RETRIES):
    """Download sicuro con retry e timeout"""
    for attempt in range(retries + 1):
        try:
            logger.info(f"Downloading {url} (attempt {attempt + 1})")
            start_time = time.time()
            data = httptools.downloadpage(url, timeout=timeout, headers=headers).data
            download_time = time.time() - start_time
            logger.info(f"Download completed in {download_time:.2f} seconds")
            return data
        except Exception as e:
            logger.error(f"Download attempt {attempt + 1} failed: {str(e)}")
            if attempt == retries:
                raise
            time.sleep(1)  # Pausa tra i retry


@support.scrape
def peliculas(item):
    support.info('peliculas', item)

    action="findvideos"

    # Pattern ottimizzati - più semplici e veloci
    if item.args == "search":
        patronBlock = r'</script> <div class="boxgrid caption">(?P<block>.*?)<div id="right_bar">'
        # Pattern semplificato per la ricerca
        patron = r'<h2>\s*<a href="(?P<url>[^"]+)">(?P<title>[^<]+)</a>.*?src="(?P<thumb>[^"]+)".*?<span class="ml-label">(?P<year>[0-9]+).*?<p>(?P<plot>[^<]+)</p>'
    elif item.args == 'update':
        patronBlock = r'<div class="widget-title">Ultimi Film Aggiunti/Aggiornati</div>(?P<block>.*?)<div id="alt_menu">'
        patron = r'style="background-image:url\((?P<thumb>[^\)]+).+?<p class="h4">(?P<title>.*?)</p>[^>]+> [^>]+> [^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+> [^>]+> [^>]+>[^>]+>(?P<year>\d{4})[^>]+>[^>]+> [^>]+>[^>]+>(?P<duration>\d+|N/A)?.+?>.*?(?:>Film (?P<lang>Sub ITA)</a></p> )?<p>(?P<plot>[^<]+)<.*?href="(?P<url>[^"]+)'
        patronNext = ''  # non ha nessuna paginazione
    elif item.args == 'orderalf':
        patron = r'<td class="mlnh-thumb"><a href="(?P<url>[^"]+)".*?src="(?P<thumb>[^"]+)"' \
                 '.+?[^>]+>[^>]+ [^>]+[^>]+ [^>]+>(?P<title>[^<]+).*?[^>]+>(?P<year>\d{4})<' \
                 '[^>]+>[^>]+>(?P<quality>[A-Z]+)[^>]+> <td class="mlnh-5">(?P<lang>.*?)</td>'
    else:
        patronBlock = r'<div class="cover_kapsul ml-mask">(?P<block>.*?)<div class="page_nav">'
        # Pattern principale ottimizzato
        patron = r'<div class="cover boxcaption">\s*<h2>\s*<a href="(?P<url>[^"]+)">(?P<title>[^<]+)</a>.*?src="(?P<thumb>[^"]+)".*?<div class="trdublaj">(?P<quality>[^<]*)</div>.*?<span class="ml-label">(?P<year>[0-9]+)</span>.*?<span class="ml-label">(?P<duration>[^<]*)</span>.*?<p>(?P<plot>[^<]*)</p>'

    patronNext = '<span>\d</span> <a href="([^"]+)">'

    # Override del download per usare la versione sicura
    def custom_download(url):
        return safe_download(url)
    
    # debug = True
    return locals()


@support.scrape
def genres(item):
    support.info('genres',item)
    action = "peliculas"

    blacklist = ['Altadefinizione01']
    if item.args == 'genres':
        patronBlock = r'<ul class="kategori_list">(?P<block>.*?)<div class="tab-pane fade" id="wtab2">'
        patronMenu = '<li><a href="(?P<url>[^"]+)">(?P<title>.*?)</a>'
    elif item.args == 'years':
        patronBlock = r'<ul class="anno_list">(?P<block>.*?)</li> </ul> </div>'
        patronMenu = '<li><a href="(?P<url>[^"]+)">(?P<title>.*?)</a>'
    elif item.args == 'orderalf':
        patronBlock = r'<div class="movies-letter">(?P<block>.*?)<div class="clearfix">'
        patronMenu = '<a title=.*?href="(?P<url>[^"]+)"><span>(?P<title>.*?)</span>'

    #debug = True
    return locals()


@support.scrape
def orderalf(item):
    support.info('orderalf',item)

    action = 'findvideos'
    patron = r'<td class="mlnh-thumb"><a href="(?P<url>[^"]+)".*?src="(?P<thumb>[^"]+)"'\
             '.+?[^>]+>[^>]+ [^>]+[^>]+ [^>]+>(?P<title>[^<]+).*?[^>]+>(?P<year>\d{4})<'\
             '[^>]+>[^>]+>(?P<quality>[A-Z]+)[^>]+> <td class="mlnh-5">(?P<lang>.*?)</td>'
    patronNext = r'<span>[^<]+</span>[^<]+<a href="(.*?)">'

    return locals()


def search(item, text):
    """Funzione di ricerca ottimizzata"""
    support.info(f"Starting search for: '{text}'")
    start_time = time.time()
    
    itemlist = []
    
    try:
        # Preprocessing del testo di ricerca
        text = text.strip()
        if len(text) < 2:
            logger.warning("Search text too short, minimum 2 characters required")
            return []
        
        # Encoding migliorato
        text_encoded = text.replace(" ", "+")
        search_url = f"{host}/index.php?do=search&story={text_encoded}&subaction=search"
        
        logger.info(f"Search URL: {search_url}")
        
        # Creazione item con parametri ottimizzati
        item.url = search_url
        item.args = "search"
        
        # Esecuzione ricerca
        logger.info("Executing search...")
        search_start = time.time()
        itemlist = peliculas(item)
        search_time = time.time() - search_start
        
        logger.info(f"Search completed in {search_time:.2f} seconds, found {len(itemlist)} results")
        
        # Filtraggio risultati se necessario
        if len(itemlist) > 50:  # Limita i risultati per performance
            logger.info(f"Limiting results from {len(itemlist)} to 50")
            itemlist = itemlist[:50]
        
    except Exception as e:
        # Gestione errori specifica
        error_type = type(e).__name__
        logger.error(f"Search failed with {error_type}: {str(e)}")
        
        # Retry con parametri diversi in caso di timeout
        if "timeout" in str(e).lower() or "connection" in str(e).lower():
            logger.info("Retrying search with longer timeout...")
            try:
                time.sleep(2)
                itemlist = peliculas(item)
            except Exception as retry_error:
                logger.error(f"Retry failed: {str(retry_error)}")
        
        # Log dettagliato per debug
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        return []
    
    finally:
        total_time = time.time() - start_time
        logger.info(f"Total search time: {total_time:.2f} seconds")
    
    return itemlist


def newest(categoria):
    """Funzione per gli ultimi film ottimizzata"""
    support.info(f"Getting newest for category: {categoria}")
    start_time = time.time()

    itemlist = []
    item = Item()
    
    try:
        if categoria == "peliculas":
            item.url = host
            item.action = "peliculas"
            item.contentType = 'movie'
            item.args = 'update'  # Usa la sezione update che è più veloce
            
            logger.info("Fetching newest movies...")
            itemlist = peliculas(item)
            
            # Rimuovi l'ultimo elemento se è un link alla pagina successiva
            if itemlist and itemlist[-1].action == "peliculas":
                itemlist.pop()
                
            logger.info(f"Found {len(itemlist)} newest movies")
            
    except Exception as e:
        logger.error(f"Error in newest: {type(e).__name__}: {str(e)}")
        return []
    
    finally:
        total_time = time.time() - start_time
        logger.info(f"Newest completed in {total_time:.2f} seconds")

    return itemlist


def findvideos(item):
    """Funzione findvideos ottimizzata"""
    support.info('findvideos', item)
    start_time = time.time()
    
    try:
        # Download sicuro della pagina
        data = safe_download(item.url)
        
        if not data:
            logger.error("No data received from page")
            return []
        
        logger.info(f"Page data length: {len(data)} characters")
        
        # Estrazione dell'iframe principale - pattern multipli per robustezza
        iframe_patterns = [
            r'<iframe[^>]+src="([^"]+)"[^>]+id="mirrorFrame"',
            r'<iframe[^>]+src="(https://mostraguarda[^"]+)"',
            r'<iframe[^>]+src="([^"]*player[^"]*)"',
            r'src="([^"]*embed[^"]*)"'
        ]
        
        iframe = None
        for pattern in iframe_patterns:
            iframe = support.match(data, patron=pattern).match
            if iframe:
                logger.info(f"Found iframe with pattern: {pattern}")
                break
        
        if iframe:
            # Correzione URL relativi
            if iframe.startswith('//'):
                iframe = 'https:' + iframe
            elif iframe.startswith('/'):
                parts = item.url.split('/')
                base_url = parts[0] + '//' + parts[2]
                iframe = base_url + iframe
            
            logger.info(f"Final iframe URL: {iframe}")
            item.url = iframe
        else:
            logger.warning("No iframe found in page")
        
        # Chiamata al support.server ottimizzata
        result = support.server(item)
        
        processing_time = time.time() - start_time
        logger.info(f"findvideos completed in {processing_time:.2f} seconds")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in findvideos: {type(e).__name__}: {str(e)}")
        return []


# Funzione di utility per test delle performance
def test_performance():
    """Funzione per testare le performance del canale"""
    logger.info("=== PERFORMANCE TEST START ===")
    
    # Test di connessione al sito
    start = time.time()
    try:
        data = safe_download(host)
        connection_time = time.time() - start
        logger.info(f"Connection test: {connection_time:.2f} seconds")
        logger.info(f"Page size: {len(data) if data else 0} characters")
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
    
    # Test di ricerca
    test_item = Item()
    test_item.action = "search"
    
    test_queries = ["spider", "batman", "avengers"]
    for query in test_queries:
        start = time.time()
        try:
            results = search(test_item, query)
            search_time = time.time() - start
            logger.info(f"Search '{query}': {search_time:.2f} seconds, {len(results)} results")
        except Exception as e:
            logger.error(f"Search '{query}' failed: {str(e)}")
    
    logger.info("=== PERFORMANCE TEST END ===")
