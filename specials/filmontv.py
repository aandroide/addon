# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale film in tv
# ------------------------------------------------------------

import re
try:
    import urllib.parse as urllib
except ImportError:
    import urllib
from core import httptools, scrapertools, support, tmdb, filetools
from core.item import Item
from platformcode import logger, config, platformtools

host = "https://www.superguidatv.it"
TIMEOUT_TOTAL = 60


def mainlist(item):
    logger.debug(" mainlist")
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
        #Item(channel=item.channel,
        #     title=config.get_setting("film2", channel="filmontv"),
        #     action="now_on_tv",
        #     url="%s/film-in-tv/oggi/premium/" % host,
        #     thumbnail=item.thumbnail),
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
        #Item(channel=item.channel,
        #     title=config.get_setting("film5", channel="filmontv"),
        #     action="now_on_tv",
        #     url="%s/film-in-tv/oggi/sky-primafila/" % host,
        #     thumbnail=item.thumbnail),
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
        #Item(channel=item.channel,
        #     title=config.get_setting("now2", channel="filmontv"),
        #     action="now_on_misc",
        #     url="%s/ora-in-onda/premium/" % host,
        #     thumbnail=item.thumbnail),
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
             action="now_on_misc_film",
             url="%s/ora-in-onda/sky-doc-e-lifestyle/" % host,
             thumbnail=item.thumbnail),
        Item(channel=item.channel,
             title=config.get_setting("now6", channel="filmontv"),
             action="now_on_misc_film",
             url="%s/ora-in-onda/sky-bambini/" % host,
             thumbnail=item.thumbnail),
        Item(channel=item.channel,
             title=config.get_setting("now7", channel="filmontv"),
             action="now_on_misc_film",
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
    
    if not text:
        return text
    
    # Prima decodifica con scrapertools
    text = scrapertools.decodeHtmlentities(text).strip()
    
    # Decodifica aggiuntiva per caratteri speciali
    try:
        import html
        text = html.unescape(text)
    except:
        pass
    
    return text


def now_on_misc_film(item):
    itemlist = []
    data = httptools.downloadpage(item.url, timeout=TIMEOUT_TOTAL).data
    
    if 'sgtvonair_divCell' in data:
        patron = (
            r'<img[^>]*class="sgtvonair_logo"[^>]*alt="([^"]+)"[^>]*>.*?'
            r'<div class="sgtvonair_divHours">([^<]+)</div>.*?'
            r'<span class="sgtvonair_spanTitle"[^>]*>([^<]+)</span>.*?'
            r'(?:<img[^>]*class="sgtvonair_backdrop"[^>]*src="([^"]+)")?.*?'
            r'(?=<hr class="sgtvonair_hr"|<div class="sgtvonair_divProgram")'
        )
        
        matches = re.findall(patron, data, re.DOTALL)
        
        for scrapedchannel, orario, scrapedtitle, scrapedthumbnail in matches:
    
            scrapedchannel = decode_html_entities(scrapedchannel)
            scrapedtitle = decode_html_entities(scrapedtitle)
            orario = decode_html_entities(orario)
            
            time_display = orario.split(' - ')[0] if ' - ' in orario else orario
            
            infoLabels = {}
            infoLabels['title'] = "movie"
            
            title_display = "[B]%s[/B] - %s - %s" % (scrapedtitle, scrapedchannel, time_display)
            
            thumb_clean = scrapedthumbnail.replace("?width=320", "?width=640") if scrapedthumbnail else ""
            if thumb_clean.startswith("//"):
                thumb_clean = "https:" + thumb_clean
            elif thumb_clean and not thumb_clean.startswith("http"):
                thumb_clean = host + thumb_clean if thumb_clean.startswith("/") else ""
            
            itemlist.append(
                Item(channel=item.channel,
                     action="new_search",
                     extra=urllib.quote_plus(scrapedtitle) + '{}' + 'movie',
                     title=title_display,
                     fulltitle=scrapedtitle,
                     mode='all',
                     search_text=scrapedtitle,
                     url="",
                     thumbnail=thumb_clean,
                     contentTitle=scrapedtitle,
                     contentType='movie',
                     infoLabels=infoLabels,
                     folder=True))
    
    if not itemlist and 'sgtvfullfilmview_divCell' in data:
        patron = r'<div class="sgtvfullfilmview_divCell"[^>]*data-date-start="([^"]+)"[^>]*>.*?'
        patron += r'<img[^>]*class="sgtvfullfilmview_logo[^"]*"[^>]*alt="([^"]+)"[^>]*>.*?'
        patron += r'<span[^>]*class="sgtvfullfilmview_spanTitleMovie"[^>]*>([^<]+)</span>.*?'
        patron += r'<img[^>]*class="sgtvfullfilmview_cover[^"]*"[^>]*alt="[^"]*"[^>]*data-src="([^"]+)"'
        
        matches = re.compile(patron, re.DOTALL).findall(data)
        
        for timestamp_start, scrapedchannel, scrapedtitle, scrapedthumbnail in matches:
            
            scrapedchannel = decode_html_entities(scrapedchannel)
            scrapedtitle = decode_html_entities(scrapedtitle)
            
            try:
                start_time = datetime.fromtimestamp(int(timestamp_start)).strftime('%H:%M')
                time_display = start_time
            except:
                time_display = ""
            
            infoLabels = {}
            infoLabels['title'] = "movie"
            
            if time_display:
                title_display = "[B]%s[/B] - %s - %s" % (scrapedtitle, scrapedchannel, time_display)
            else:
                title_display = "[B]%s[/B] - %s" % (scrapedtitle, scrapedchannel)
            
            if scrapedthumbnail:
                scrapedthumbnail = scrapedthumbnail.replace("?width=320", "?width=640")
                if scrapedthumbnail.startswith('//'):
                    scrapedthumbnail = 'https:' + scrapedthumbnail
                elif not scrapedthumbnail.startswith('http'):
                    scrapedthumbnail = host + scrapedthumbnail if scrapedthumbnail.startswith('/') else ""
            
            itemlist.append(
                Item(channel=item.channel,
                     action="new_search",
                     extra=urllib.quote_plus(scrapedtitle) + '{}' + 'movie',
                     title=title_display,
                     fulltitle=scrapedtitle,
                     mode='all',
                     search_text=scrapedtitle,
                     url="",
                     thumbnail=scrapedthumbnail,
                     contentTitle=scrapedtitle,
                     contentType='movie',
                     infoLabels=infoLabels,
                     folder=True))
    
    if not itemlist:
        logger.error("Nessun film trovato per URL: %s" % item.url)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def now_on_misc(item):
    itemlist = []

    try:
        data = httptools.downloadpage(item.url, timeout=TIMEOUT_TOTAL).data
        
        if 'sgtvonair' in data:
            patron = (
                r'<img[^>]*class="sgtvonair_logo"[^>]*alt="([^"]+)"[^>]*>.*?'
                r'(?:<a class="sgtvonair_eventLink"[^>]*>.*?)?'
                r'<div class="sgtvonair_divHours">([^<]+)</div>.*?'
                r'<span class="sgtvonair_spanTitle"[^>]*>([^<]+)</span>.*?'
                r'(?:<img[^>]*class="sgtvonair_backdrop"[^>]*src="([^"]+)")?.*?'
                r'(?=<hr class="sgtvonair_hr"|<div class="sgtvonair_divProgram")'
            )
            
            matches = re.findall(patron, data, re.DOTALL)
            
            for canale, orario, titolo, thumb in matches:
                
                canale = decode_html_entities(canale)
                titolo = decode_html_entities(titolo)
                orario = decode_html_entities(orario)
                
                if ' - ' in orario:
                    orario = orario.split(' - ')[0]
                
                thumb_clean = thumb.replace("?width=320", "?width=640") if thumb else ""
                if thumb_clean.startswith("//"):
                    thumb_clean = "https:" + thumb_clean
                elif thumb_clean and not thumb_clean.startswith("http"):
                    thumb_clean = host + thumb_clean if thumb_clean.startswith("/") else ""
                
                title_display = "[B]%s[/B] - %s - %s" % (titolo, canale, orario)
                
                itemlist.append(
                    Item(channel=item.channel,
                         action="new_search",
                         extra=urllib.quote_plus(titolo) + '{}' + 'tvshow',
                         title=title_display,
                         fulltitle=titolo,
                         mode='all',
                         search_text=titolo,
                         url="",
                         thumbnail=thumb_clean,
                         contentTitle=titolo,
                         contentType='tvshow',
                         infoLabels={'tvshowtitle': titolo, 'year': ''},
                         folder=True))
        
        elif 'sgtvfullfilmview_divCell' in data:
            patron = r'<div class="sgtvfullfilmview_divCell"[^>]*data-date-start="([^"]+)"[^>]*>.*?'
            patron += r'<img[^>]*class="sgtvfullfilmview_logo[^"]*"[^>]*alt="([^"]+)"[^>]*>.*?'
            patron += r'<span[^>]*class="sgtvfullfilmview_spanTitleMovie"[^>]*>([^<]+)</span>.*?'
            patron += r'<img[^>]*class="sgtvfullfilmview_cover[^"]*"[^>]*alt="[^"]*"[^>]*data-src="([^"]+)"'
            
            matches = re.compile(patron, re.DOTALL).findall(data)
            logger.info("Trovati %d matches con pattern timestamp" % len(matches))
        
            for timestamp_start, scrapedchannel, scrapedtitle, scrapedthumbnail in matches:
                
                scrapedchannel = decode_html_entities(scrapedchannel)
                scrapedtitle = decode_html_entities(scrapedtitle)
                
                try:
                    start_time = datetime.fromtimestamp(int(timestamp_start)).strftime('%H:%M')
                    time_display = start_time
                except Exception as e:
                    logger.error("Errore calcolo orario: %s" % str(e))
                    time_display = ""
                
                thumb_clean = scrapedthumbnail.replace("?width=320", "?width=640") if scrapedthumbnail else ""
                if thumb_clean.startswith("//"):
                    thumb_clean = "https:" + thumb_clean
                elif thumb_clean and not thumb_clean.startswith("http"):
                    thumb_clean = host + thumb_clean if thumb_clean.startswith("/") else ""
                
                if time_display:
                    title_display = "[B]%s[/B] - %s - %s" % (scrapedtitle, scrapedchannel, time_display)
                else:
                    title_display = "[B]%s[/B] - %s" % (scrapedtitle, scrapedchannel)
                
                itemlist.append(
                    Item(channel=item.channel,
                         action="new_search",
                         extra=urllib.quote_plus(scrapedtitle) + '{}' + 'tvshow',
                         title=title_display,
                         fulltitle=scrapedtitle,
                         mode='all',
                         search_text=scrapedtitle,
                         url="",
                         thumbnail=thumb_clean,
                         contentTitle=scrapedtitle,
                         contentType='tvshow',
                         infoLabels={'tvshowtitle': scrapedtitle, 'year': ''},
                         folder=True))
        
        if not itemlist:
            logger.warning("Nessun programma trovato per URL: %s" % item.url)
    
    except Exception as e:
        logger.error("Errore in now_on_misc: %s" % str(e))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def now_on_tv(item):
    itemlist = []
    
    try:
        data = httptools.downloadpage(item.url, timeout=TIMEOUT_TOTAL).data
        
        block_pattern = r'(<div class="sgtvfullfilmview_divProgram.*?</div>\s*</div>\s*</div>)'
        blocks = re.findall(block_pattern, data, re.DOTALL)
        
        if not blocks:
            logger.warning("Nessun blocco trovato per URL: %s" % item.url)
            return itemlist
        
        for block in blocks:
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
                
                if scrapedthumbnail:
                    scrapedthumbnail = scrapedthumbnail.replace("?width=240", "?width=480").replace("?width=320", "?width=640")
                    if scrapedthumbnail.startswith('//'):
                        scrapedthumbnail = 'https:' + scrapedthumbnail
                    elif not scrapedthumbnail.startswith('http'):
                        scrapedthumbnail = host + scrapedthumbnail if scrapedthumbnail.startswith('/') else ""
                
                infoLabels = {
                    'year': scrapedyear,
                    'genre': scrapedgenre
                }
                
                title_parts = ["[B]%s[/B]" % scrapedtitle]
                if scrapedchannel:
                    title_parts.append(scrapedchannel)
                if scrapedtime:
                    title_parts.append(scrapedtime)
                
                title_display = " - ".join(title_parts)
                
                itemlist.append(
                    Item(channel=item.channel,
                         action="new_search",
                         extra=urllib.quote_plus(scrapedtitle) + '{}' + 'movie',
                         title=title_display,
                         fulltitle=scrapedtitle,
                         mode='all',
                         search_text=scrapedtitle,
                         url="",
                         thumbnail=scrapedthumbnail,
                         contentTitle=scrapedtitle,
                         contentType='movie',
                         infoLabels=infoLabels,
                         folder=True)
                )
    
    except Exception as e:
        logger.error("Errore in now_on_tv: %s" % str(e))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def new_search(item):
    from specials import search
    return search.new_search(item)


def live(item):
    import sys
    import channelselector
    
    if sys.version_info[0] >= 3:
        from concurrent import futures
    else:
        from concurrent_py2 import futures
    
    itemlist = []
    channels_dict = {}
    channels = channelselector.filterchannels('live')
    
    with futures.ThreadPoolExecutor() as executor:
        itlist = [executor.submit(load_live, ch.channel) for ch in channels]
        for res in futures.as_completed(itlist):
            if res.result():
                channel_name, itlist = res.result()
                channels_dict[channel_name] = itlist
    
    channel_list = ['raiplay', 'mediasetplay', 'la7', 'discoveryplus']
    
    for ch in channels:
        if ch.channel not in channel_list:
            channel_list.append(ch.channel)
    
    for ch in channel_list:
        if ch in channels_dict:
            itemlist += channels_dict[ch]
    
    itemlist.sort(key=lambda it: support.channels_order.get(it.fulltitle, 1000))
    return itemlist


def load_live(channel_name):
    try:
        channel = __import__('%s.%s' % ('channels', channel_name), None, None, ['%s.%s' % ('channels', channel_name)])
        itemlist = channel.live(channel.mainlist(Item())[0])
    except:
        itemlist = []
    return channel_name, itemlist
