# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale film in tv - VERSIONE 3.0 by Aandroide
# ------------------------------------------------------------

import re
import sys
try:
    import urllib.parse as urllib
except ImportError:
    import urllib

from core import httptools, scrapertools, support, tmdb, filetools
from core.item import Item
from platformcode import logger, config, platformtools

if sys.version_info[0] >= 3:
    from concurrent import futures
else:
    from concurrent_py2 import futures

host = "https://www.superguidatv.it"
TIMEOUT_TOTAL = 30  #  Ridotto da 60 a 30 secondi
TIMEOUT_DETAIL = 5  #  Timeout ridotto per pagine dettaglio

#  CACHE PER EVITARE CHIAMATE DUPLICATE
_detail_cache = {}

#  REGEX PRECOMPILATE (molto più veloce)
RE_CHANNEL = re.compile(r'<img[^>]*class="sgtvonair_logo"[^>]*alt="([^"]+)"')
RE_BACKDROP = re.compile(r'<img[^>]*class="sgtvonair_backdrop"[^>]*src="([^"]+)"')
RE_ALT_IMG = re.compile(r'<img[^>]*src="([^"]+)"[^>]*class="sgtvonair')
RE_PROGRAMS = re.compile(
    r'<div class="sgtvonair_divProgram sgtvonair_displayTable">.*?'
    r'<div class="sgtvonair_divHours">([^<]+)</div>.*?'
    r'<span class="sgtvonair_spanTitle"[^>]*>([^<]+)</span>.*?'
    r'(?:<span class="sgtvonair_spanEventTypeFromTime"[^>]*>\(da ([^)]+)\)</span>)?',
    re.DOTALL
)
RE_EVENT_LINK = re.compile(r'<a class="sgtvonair_eventLink"[^>]*href="([^"]+)"')
RE_YEAR_IN_TITLE = re.compile(r'\((\d{4})\)')
RE_DESC_PATTERNS = [
    re.compile(r'<div class="sgtvdetails_divContentText">([^<]+)</div>'),
    re.compile(r'<div class="sgtvdetails_divContentText[^"]*">(.*?)</div>'),
]
RE_YEAR_PATTERNS = [
    re.compile(r'<div class="sgtvdetails_divMovieInfoRow[^>]*>\s*<div[^>]*>.*?(\d{4})</div>'),
    re.compile(r'US\s*&nbsp;(\d{4})'),
    re.compile(r'IT\s*&nbsp;(\d{4})'),
    re.compile(r'GB\s*&nbsp;(\d{4})'),
]

#  PLACEHOLDER INDICATORS PRECOMPILATI
PLACEHOLDER_INDICATORS = frozenset([
    'repliche', 'programmazione', 'palinsesto', 'in onda dalle',
    'messa in onda', 'trasmissione', 'programmi di', 'replica'
])


def mainlist(item):
    logger.debug()
    itemlist = [
        Item(title=support.typo('Canali live', 'bold'),
             channel=item.channel,
             action='live',
             thumbnail=support.thumb('tvshow_on_the_air')),

        Item(channel=item.channel,
             title=config.get_setting("film1", channel="filmontv"),
             action="now_on_tv",
             url="%s/film-in-tv/" % host,
             thumbnail=item.thumbnail),
        Item(channel=item.channel,
             title=config.get_setting("film3", channel="filmontv"),
             action="now_on_tv",
             url="%s/film-in-tv/oggi/sky-intrattenimento/" % host,
             thumbnail=item.thumbnail),
        Item(channel=item.channel,
             title=config.get_setting("film4", channel="filmontv"),
             action="now_on_tv",
             url="%s/film-in-tv/oggi/sky-cinema/" % host,
             thumbnail=item.thumbnail),
        Item(channel=item.channel,
             title=config.get_setting("film6", channel="filmontv"),
             action="now_on_tv",
             url="%s/film-in-tv/oggi/sky-doc-e-lifestyle/" % host,
             thumbnail=item.thumbnail),
        Item(channel=item.channel,
             title=config.get_setting("film7", channel="filmontv"),
             action="now_on_tv",
             url="%s/film-in-tv/oggi/sky-bambini/" % host,
             thumbnail=item.thumbnail),

        Item(channel=item.channel,
             title=config.get_setting("now1", channel="filmontv"),
             action="now_on_misc",
             url="%s/ora-in-onda/" % host,
             thumbnail=item.thumbnail),
        Item(channel=item.channel,
             title=config.get_setting("now3", channel="filmontv"),
             action="now_on_misc",
             url="%s/ora-in-onda/sky-intrattenimento/" % host,
             thumbnail=item.thumbnail),
        Item(channel=item.channel,
             title=config.get_setting("now4", channel="filmontv"),
             action="now_on_misc",
             url="%s/ora-in-onda/sky-cinema/" % host,
             thumbnail=item.thumbnail),
        Item(channel=item.channel,
             title=config.get_setting("now5", channel="filmontv"),
             action="now_on_misc",
             url="%s/ora-in-onda/sky-doc-e-lifestyle/" % host,
             thumbnail=item.thumbnail),
        Item(channel=item.channel,
             title=config.get_setting("now6", channel="filmontv"),
             action="now_on_misc",
             url="%s/ora-in-onda/sky-bambini/" % host,
             thumbnail=item.thumbnail),
        Item(channel=item.channel,
             title=config.get_setting("now7", channel="filmontv"),
             action="now_on_misc",
             url="%s/ora-in-onda/rsi/" % host,
             thumbnail=item.thumbnail),

        Item(channel=item.channel,
             title="Personalizza Oggi in TV",
             action="server_config",
             config="filmontv",
             folder=False,
             thumbnail=item.thumbnail)
    ]
    return itemlist


def server_config(item):
    return platformtools.show_channel_settings(channelpath=filetools.join(config.get_runtime_path(), "specials", item.config))


def decode_html_entities(text):
    """Decodifica entità HTML - OTTIMIZZATA"""
    if not text:
        return text

    text = scrapertools.decodeHtmlentities(text).strip()

    try:
        import html
        return html.unescape(text)
    except:
        return text


def clean_thumbnail(thumb_url):
    """Pulisce e valida URL delle thumbnail - OTTIMIZZATA"""
    if not thumb_url:
        return ""

    #  BLACKLIST come frozenset (più veloce)
    blacklist = frozenset([
        'cover-placeholder.png',
        'placeholder.png',
        'no-image.png',
        'default-cover.png',
        'default.jpg',
        'placeholder.jpg'
    ])

    thumb_clean = thumb_url.strip()
    
    if thumb_clean.startswith("//"):
        thumb_clean = "https:" + thumb_clean
    elif not thumb_clean.startswith("http"):
        if thumb_clean.startswith("/"):
            thumb_clean = host + thumb_clean
        else:
            return ""

    #  Check blacklist ottimizzato
    thumb_lower = thumb_clean.lower()
    if any(blocked in thumb_lower for blocked in blacklist):
        return ""

    if "?width=" in thumb_clean:
        thumb_clean = re.sub(r'\?width=\d+', '?width=480', thumb_clean)
    
    return thumb_clean


def is_valid_year(year_str):
    """Verifica anno valido - OTTIMIZZATA"""
    try:
        year_int = int(year_str)
        from datetime import datetime
        return 1900 <= year_int <= datetime.now().year + 2
    except:
        return False


def get_program_description_and_year(detail_url):
    """
     VERSIONE OTTIMIZZATA con CACHE e TIMEOUT RIDOTTO
    """
    #  CACHE: evita chiamate duplicate
    if detail_url in _detail_cache:
        return _detail_cache[detail_url]
    
    try:
        detail_data = httptools.downloadpage(detail_url, timeout=TIMEOUT_DETAIL).data
        
        descrizione = ""
        anno = ""
        
        #  Usa regex precompilate
        for pattern in RE_DESC_PATTERNS:
            desc_match = pattern.search(detail_data)
            if desc_match:
                descrizione = decode_html_entities(desc_match.group(1).strip())
                break
        
        #  Estrazione anno con regex precompilate
        for pattern in RE_YEAR_PATTERNS:
            year_matches = pattern.findall(detail_data)
            if year_matches:
                for year_candidate in year_matches:
                    if is_valid_year(year_candidate):
                        anno = year_candidate
                        break
                if anno:
                    break
        
        #  Salva in cache
        result = (descrizione, anno)
        _detail_cache[detail_url] = result
        return result
            
    except Exception as e:
        logger.debug("⚠️ Errore recupero descrizione e anno: %s" % str(e))
        result = ("", "")
        _detail_cache[detail_url] = result
        return result


def now_on_misc(item):
    """
     VERSIONE OTTIMIZZATA - Gestisce CONTENUTI MISTI
    """
    logger.debug()
    itemlist = []
    processed_channels = set()

    try:
        data = httptools.downloadpage(item.url, timeout=TIMEOUT_TOTAL).data
    except Exception as e:
        logger.error("Errore download: %s" % str(e))
        return itemlist

    blocks = re.findall(r'<div class="sgtvonair_divContent">(.*?)</div>\s*</div>\s*</div>', data, re.DOTALL)

    #  PROCESSING PARALLELO dei dettagli (se necessario)
    detail_urls_to_fetch = []
    
    for block_html in blocks:
        try:
            #  Usa regex precompilate
            channel_match = RE_CHANNEL.search(block_html)
            if not channel_match:
                continue
                
            canale = decode_html_entities(channel_match.group(1))
            
            if canale in processed_channels:
                continue

            backdrop_match = RE_BACKDROP.search(block_html)
            thumb = backdrop_match.group(1) if backdrop_match else ""
            
            thumb_clean = clean_thumbnail(thumb) if thumb else ""
            
            if not thumb_clean:
                alt_img_match = RE_ALT_IMG.search(block_html)
                if alt_img_match:
                    thumb_clean = clean_thumbnail(alt_img_match.group(1))

            all_programs = RE_PROGRAMS.findall(block_html)

            if not all_programs:
                continue

            from datetime import datetime, timedelta
            
            programma_scelto = None
            now = datetime.now()
            
            #  PASSA 1: Cerca programmi con "da X minuti/ore"
            for prog in all_programs:
                tempo_prog = prog[2] if prog[2] else ""
                
                if tempo_prog and ("min" in tempo_prog or "ora" in tempo_prog or "ore" in tempo_prog):
                    programma_scelto = prog
                    break
            
            #  PASSA 2: Analizza orari (SEMPLIFICATO)
            if not programma_scelto:
                programmi_validi = []
                
                for prog in all_programs:
                    orario_prog = decode_html_entities(prog[0]).strip()
                    titolo_prog = decode_html_entities(prog[1]).strip()

                    #  Check placeholder ottimizzato
                    titolo_lower = titolo_prog.lower()
                    if any(indicator in titolo_lower for indicator in PLACEHOLDER_INDICATORS):
                        continue
                    
                    if re.match(r'^[-:]+$', orario_prog):
                        continue
                    
                    try:
                        if ' - ' in orario_prog:
                            start_time_str = orario_prog.split(' - ')[0].strip()
                        else:
                            start_time_str = orario_prog.strip()
                        
                        start_time = datetime.strptime(start_time_str, '%H:%M').replace(
                            year=now.year, month=now.month, day=now.day
                        )
                        
                        if start_time.hour >= 0 and start_time.hour < 6 and now.hour >= 18:
                            start_time += timedelta(days=1)
                        
                        if start_time <= now:
                            programmi_validi.append({
                                'prog': prog,
                                'start': start_time,
                                'is_current': True,
                                'distance': (now - start_time).total_seconds()
                            })
                        else:
                            programmi_validi.append({
                                'prog': prog,
                                'start': start_time,
                                'is_current': False,
                                'distance': (start_time - now).total_seconds()
                            })
                    
                    except Exception:
                        continue
                
                if programmi_validi:
                    programmi_validi.sort(key=lambda x: (not x['is_current'], abs(x['distance'])))
                    programma_scelto = programmi_validi[0]['prog']
            
            #  FALLBACK
            if not programma_scelto:
                for prog in all_programs:
                    titolo_prog = decode_html_entities(prog[1]).strip()
                    if not any(indicator in titolo_prog.lower() for indicator in PLACEHOLDER_INDICATORS):
                        programma_scelto = prog
                        break

            if not programma_scelto and all_programs:
                programma_scelto = all_programs[0]

            if not programma_scelto:
                continue

            orario = decode_html_entities(programma_scelto[0])
            titolo = decode_html_entities(programma_scelto[1])
            tempo = programma_scelto[2] if programma_scelto[2] else ""

            if ' - ' in orario:
                orario = orario.split(' - ')[0]

            #  ESTRAI URL DETTAGLIO
            detail_url = ""
            first_event_match = RE_EVENT_LINK.search(block_html)
            if first_event_match:
                detail_url = first_event_match.group(1)

            #  Prepara lista URL da scaricare in parallelo (OPZIONALE)
            if detail_url and "repliche" not in titolo.lower() and detail_url not in _detail_cache:
                detail_urls_to_fetch.append((detail_url, canale, titolo))

            descrizione = ""
            anno = ""
            if detail_url and "repliche" not in titolo.lower():
                descrizione, anno = get_program_description_and_year(detail_url)

            if tempo:
                title_display = "[B]%s[/B] %s %s (da %s)" % (titolo, canale, orario, tempo)
            else:
                title_display = "[B]%s[/B] %s %s" % (titolo, canale, orario)

            year_from_title = ""
            title_clean = titolo
            year_match = RE_YEAR_IN_TITLE.search(titolo)
            if year_match:
                year_candidate = year_match.group(1)
                if is_valid_year(year_candidate):
                    year_from_title = year_candidate
                    title_clean = RE_YEAR_IN_TITLE.sub('', titolo).strip()

            anno_finale = anno if anno else year_from_title

            itemlist.append(create_search_item(
                title=title_display,
                search_text=title_clean,
                content_type='undefined',
                thumbnail=thumb_clean,
                year=anno_finale,
                plot=descrizione
            ))
            
            processed_channels.add(canale)
            
        except Exception as e:
            logger.error("❌ Errore blocco: %s" % str(e))
            continue

    #  SALVA THUMBNAIL E PLOT ORIGINALI
    for it in itemlist:
        it._site_thumbnail = getattr(it, 'thumbnail', "")
        it._site_plot = getattr(it, 'plot', "")

    #  TMDB solo per elementi con anno
    with_year = [it for it in itemlist if getattr(it, 'contentYear', '')]
    without_year = [it for it in itemlist if not getattr(it, 'contentYear', '')]

    if with_year:
        try:
            tmdb.set_infoLabels_itemlist(with_year, seekTmdb=True)
        except Exception as e:
            logger.error("❌ Errore TMDB: %s" % str(e))

    for it in without_year:
        if not getattr(it, 'infoLabels', None):
            it.infoLabels = {
                'title': getattr(it, 'contentTitle', ''),
                'year': '',
                'genre': '',
                'plot': getattr(it, 'plot', '')
            }

    #  PRIORITÀ THUMBNAIL E PLOT
    for it in itemlist:
        original_thumb = getattr(it, '_site_thumbnail', "")
        original_plot = getattr(it, '_site_plot', "")
        tmdb_thumb = getattr(it, 'thumbnail', "")
        tmdb_plot = it.infoLabels.get('plot', '') if getattr(it, 'infoLabels', None) else ""

        if getattr(it, 'contentYear', '') and tmdb_thumb and ('themoviedb.org' in tmdb_thumb or 'image.tmdb.org' in tmdb_thumb):
            it.thumbnail = tmdb_thumb
            it.plot = tmdb_plot if tmdb_plot and tmdb_plot.strip() else original_plot
            if hasattr(it, 'infoLabels') and it.infoLabels:
                it.infoLabels['plot'] = it.plot
        elif original_thumb and original_thumb.strip():
            it.thumbnail = original_thumb
            it.plot = original_plot
        else:
            it.thumbnail = ""
            it.plot = original_plot

    return itemlist


def now_on_tv(item):
    """ VERSIONE OTTIMIZZATA - Gestisce SOLO FILM"""
    logger.debug()
    itemlist = []

    try:
        data = httptools.downloadpage(item.url, timeout=TIMEOUT_TOTAL).data
    except Exception as e:
        logger.error("Errore download: %s" % str(e))
        return itemlist

    block_pattern = r'(<div class="sgtvfullfilmview_divProgram.*?</div>\s*</div>\s*</div>)'
    blocks = re.findall(block_pattern, data, re.DOTALL)

    if not blocks:
        return itemlist

    for block in blocks:
        try:
            channel_match = re.search(r'sgtvfullfilmview_logo[^>]*alt="([^"]+)"', block)
            scrapedchannel = decode_html_entities(channel_match.group(1)) if channel_match else ""

            time_match = re.search(r'<span[^>]*class="sgtvfullfilmview_spanMovieDuration"[^>]*>(\d{2}:\d{2}\s*-\s*\d{2}:\d{2})</span>', block)
            scrapedtime = decode_html_entities(time_match.group(1)) if time_match else ""

            title_match = re.search(r'sgtvfullfilmview_spanTitleMovie[^>]*>([^<]+)</span>', block)
            scrapedtitle = decode_html_entities(title_match.group(1)) if title_match else ""

            genre_match = re.search(r'sgtvfullfilmview_spanDirectorGenresMovie[^>]*>\s*([^<]+)</span>', block)
            scrapedgenre = decode_html_entities(genre_match.group(1)) if genre_match else ""

            thumb_match = re.search(r'sgtvfullfilmview_cover[^>]*data-src="([^"]+)"', block)
            scrapedthumbnail = decode_html_entities(thumb_match.group(1)) if thumb_match else ""

            year_match = re.search(r'sgtvfullfilmview_divMovieYear[^>]*>(?:[A-Z,\s]*)?([0-9]{4})', block)
            scrapedyear = decode_html_entities(year_match.group(1)) if year_match else ""

            if scrapedtitle and len(scrapedtitle) > 2:
                thumb_clean = clean_thumbnail(scrapedthumbnail)

                title_parts = ["[B]%s[/B]" % scrapedtitle]
                if scrapedchannel:
                    title_parts.append(scrapedchannel)
                if scrapedtime:
                    title_parts.append(scrapedtime)

                title_display = " ".join(title_parts)

                itemlist.append(create_search_item(
                    title=title_display,
                    search_text=scrapedtitle,
                    content_type='movie',
                    thumbnail=thumb_clean,
                    year=scrapedyear,
                    genre=scrapedgenre
                ))
        except Exception:
            continue

    if not itemlist:
        return itemlist

    #  Salva thumbnail originali
    for it in itemlist:
        it._site_thumbnail = getattr(it, 'thumbnail', "")

    try:
        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    except Exception as e:
        logger.error("❌ Errore TMDB: %s" % str(e))

    #  Gestione thumbnail
    for it in itemlist:
        original_thumb = getattr(it, '_site_thumbnail', "")
        tmdb_thumb = getattr(it, 'thumbnail', "")

        if tmdb_thumb and ('themoviedb.org' in tmdb_thumb or 'image.tmdb.org' in tmdb_thumb):
            it.thumbnail = tmdb_thumb
        elif original_thumb and original_thumb.strip():
            it.thumbnail = original_thumb
        else:
            it.thumbnail = ""

    return itemlist


def create_search_item(title, search_text, content_type, thumbnail="", year="", genre="", plot=""):
    """Crea item ricerca - OTTIMIZZATA"""
    use_new_search = config.get_setting('new_search')
    clean_text = search_text.replace("+", " ").strip()

    infoLabels = {
        'year': year if year else "",
        'genre': genre if genre else "",
        'title': clean_text,
        'plot': plot if plot else ""
    }

    if content_type == 'undefined':
        infoLabels['tvshowtitle'] = clean_text
    elif content_type == 'tvshow':
        infoLabels['tvshowtitle'] = clean_text

    if use_new_search:
        new_item = Item(
            channel='globalsearch',
            action='Search',
            text=clean_text,
            title=title,
            thumbnail=thumbnail,
            fanart=thumbnail,
            mode='all',
           #type='movie' if content_type == 'movie' else 'tv',
            contentType=content_type,
            contentTitle=clean_text,
            contentYear=year if year else "",
            contentGenre=genre if genre else "",
            search_text=clean_text,
            infoLabels=infoLabels
          
        )

        if content_type in ['undefined', 'tvshow']:
            new_item.contentSerieName = clean_text

    else:
        extra_type = 'movie' if content_type in ['movie', 'undefined'] else 'tvshow'

        try:
            quote_fn = urllib.quote_plus
        except Exception:
            from urllib.parse import quote_plus as quote_fn

        new_item = Item(
            channel='search',
            action="new_search",
            extra=quote_fn(clean_text) + '{}' + extra_type,
            title=title,
            fulltitle=clean_text,
            mode='all',
            search_text=clean_text,
            url="",
            thumbnail=thumbnail,
            contentTitle=clean_text,
            contentYear=year if year else "",
            contentGenre=genre if genre else "",
            contentType=content_type,
            infoLabels=infoLabels
         
        )

        if content_type in ['undefined', 'tvshow']:
            new_item.contentSerieName = clean_text

    return new_item


def live(item):
    """Carica canali live con gestione parallela"""
    logger.debug()
    import channelselector

    itemlist = []
    channels_dict = {}
    channels = channelselector.filterchannels('live')

    with futures.ThreadPoolExecutor() as executor:
        future_list = [executor.submit(load_live, ch.channel) for ch in channels]

        for future in futures.as_completed(future_list):
            try:
                result = future.result()
                if result:
                    channel_name, channel_items = result
                    if channel_items:
                        channels_dict[channel_name] = channel_items
            except Exception as e:
                logger.error("Errore live: %s" % str(e))
                continue

    channel_list = ['raiplay', 'mediasetplay', 'la7', 'discoveryplus']

    for ch in channels:
        if ch.channel not in channel_list:
            channel_list.append(ch.channel)

    for ch in channel_list:
        if ch in channels_dict:
            itemlist += channels_dict[ch]

    try:
        itemlist.sort(key=lambda it: support.channels_order.get(it.fulltitle, 1000))
    except Exception as e:
        logger.error("Errore sort: %s" % str(e))

    return itemlist


def load_live(channel_name):
    """Carica canali live da singolo canale"""
    try:
        channel = __import__('%s.%s' % ('channels', channel_name), None, None, ['%s.%s' % ('channels', channel_name)])
        mainlist_items = channel.mainlist(Item())

        if mainlist_items:
            itemlist = channel.live(mainlist_items[0])
            return channel_name, itemlist
        else:
            return channel_name, []

    except Exception as e:
        logger.error("Errore %s: %s" % (channel_name, str(e)))
        return channel_name, []
