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
    itemlist = [#Item(channel="search", action='discover_list', title=config.get_localized_string(70309),
               #search_type='list', list_type='movie/now_playing',
               #          thumbnail=get_thumb("now_playing.png")),
               #Item(channel="search", action='discover_list', title=config.get_localized_string(70312),
               #          search_type='list', list_type='tv/on_the_air', thumbnail=get_thumb("on_the_air.png")),
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
             action="now_on_misc_film",
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


def create_search_item(title, search_text, content_type, thumbnail="", year="", genre="", plot=""):
    """
    Crea un item di ricerca che supporta sia la nuova ricerca globale che la vecchia ricerca.
    Controlla il setting 'new_search' per decidere quale usare.
    
    Nuova ricerca globale:
    - channel='globalsearch'
    - action='Search'
    - mode='all'
    - contentType='movie' o 'tvshow'
    
    Vecchia ricerca:
    - channel='search'
    - action='new_search'
    - mode='all'
    """
    use_new_search = config.get_setting('new_search')
    clean_text = search_text.replace("+", " ").strip()

    infoLabels = {
        'year': year if year else "",
        'genre': genre if genre else "",
        'title': clean_text,
        'plot': plot if plot else ""
    }

    if content_type == 'tvshow':
        infoLabels['tvshowtitle'] = clean_text

    if use_new_search:
        # NUOVA RICERCA GLOBALE
        new_item = Item(
            channel='globalsearch',
            action='Search',
            text=clean_text,
            title=title,
            thumbnail=thumbnail,
            fanart=thumbnail,
            mode='movie' if content_type == 'movie' else 'tvshow',     
            type='movie' if content_type == 'movie' else 'tvshow',                                                  
            contentType=content_type,
            infoLabels=infoLabels,
            folder=False
        )

        # Imposta contentTitle o contentSerieName
        if content_type == 'movie':
            new_item.contentTitle = clean_text
        elif content_type == 'tvshow':
            new_item.contentSerieName = clean_text

    else:
        # VECCHIA RICERCA
        try:
            quote_fn = urllib.quote_plus
        except:
            from urllib.parse import quote_plus as quote_fn

        extra_type = 'movie' if content_type == 'movie' else 'tvshow'

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
            contentType=content_type,
            infoLabels=infoLabels,
            folder=True
        )

    return new_item


def now_on_misc_film(item):
    logger.debug("filmontv now_on_misc_film")
    itemlist = []

    # Carica la pagina
    data = httptools.downloadpage(item.url).data.replace('\n', '')
    
    # Nuova regex per la struttura "ora in onda"
    patron = r'<div class="sgtvonair_divCell[^>]*>.*?'
    patron += r'sgtvonair_logo[^>]*alt="([^"]*)"[^>]*>.*?'
    patron += r'sgtvonair_divHours">([^<]*)</div>.*?'
    patron += r'sgtvonair_spanTitle[^>]*>([^<]*)</span>.*?'
    patron += r'sgtvonair_backdrop[^>]*src="([^"]*)"'
    
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    for scrapedchannel, scrapedtime, scrapedtitle, scrapedthumbnail in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        
        itemlist.append(create_search_item(
            title="[B]" + scrapedtitle + "[/B] - " + scrapedchannel + " - " + scrapedtime,
            search_text=scrapedtitle,
            content_type='movie',
            thumbnail=scrapedthumbnail if scrapedthumbnail.startswith('http') else host + scrapedthumbnail
        ))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def now_on_misc(item):
    logger.debug("filmontv now_on_misc")
    itemlist = []

    # Carica la pagina
    data = httptools.downloadpage(item.url).data.replace('\n', '')
    
    # Nuova regex per la struttura "ora in onda"
    patron = r'<div class="sgtvonair_divCell[^>]*>.*?'
    patron += r'sgtvonair_logo[^>]*alt="([^"]*)"[^>]*>.*?'
    patron += r'sgtvonair_divHours">([^<]*)</div>.*?'
    patron += r'sgtvonair_spanTitle[^>]*>([^<]*)</span>.*?'
    patron += r'sgtvonair_backdrop[^>]*src="([^"]*)"'
    
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    for scrapedchannel, scrapedtime, scrapedtitle, scrapedthumbnail in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        
        itemlist.append(create_search_item(
            title="[B]" + scrapedtitle + "[/B] - " + scrapedchannel + " - " + scrapedtime,
            search_text=scrapedtitle,
            content_type='tvshow',
            thumbnail=scrapedthumbnail if scrapedthumbnail.startswith('http') else host + scrapedthumbnail
        ))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def now_on_tv(item):
    logger.debug("filmontv tvoggi")
    itemlist = []

    # Carica la pagina
    data = httptools.downloadpage(item.url).data.replace('\n','')
    
    # Nuova regex per la nuova struttura del sito
    patron = r'<div class="sgtvfullfilmview_divCell[^>]*>.*?'
    patron += r'sgtvfullfilmview_logo[^>]*alt="([^"]*)"[^>]*>.*?'
    patron += r'sgtvfullfilmview_spanMovieDuration">([^<]*)</span>.*?'
    patron += r'sgtvfullfilmview_spanTitleMovie">([^<]*)</span>.*?'
    patron += r'sgtvfullfilmview_spanDirectorGenresMovie">[^<]*</span>.*?'
    patron += r'sgtvfullfilmview_spanDirectorGenresMovie">([^<]*)</span>.*?'
    patron += r'sgtvfullfilmview_cover[^>]*data-src="([^"]*)"[^>]*>.*?'
    patron += r'sgtvfullfilmview_divMovieYear">[^<]*([0-9]{4})'
    
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    for scrapedchannel, scrapedduration, scrapedtitle, scrapedgender, scrapedthumbnail, scrapedyear in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        
        itemlist.append(create_search_item(
            title="[B]" + scrapedtitle + "[/B] - " + scrapedchannel + " - " + scrapedduration,
            search_text=scrapedtitle,
            content_type='movie',
            thumbnail=scrapedthumbnail.replace("?width=240", "?width=480"),
            year=scrapedyear,
            genre=scrapedgender
        ))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def primafila(item):
    logger.debug("filmontv tvoggi")
    itemlist = []

    # Carica la pagina
    data = httptools.downloadpage(item.url).data
    patron = r'spanTitleMovie">([A-Za-z À-ÖØ-öø-ÿ\-\']*)[a-z \n<>\/="_\-:0-9;A-Z.]*GenresMovie">([\-\'A-Za-z À-ÖØ-öø-ÿ\/]*)[a-z \n<>\/="_\-:0-9;A-Z.%]*src="([a-zA-Z:\/\.0-9?]*)[a-z \n<>\/="_\-:0-9;A-Z.%\-\']*Year">([A-Z 0-9a-z]*)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    for scrapedtitle, scrapedgender, scrapedthumbnail, scrapedyear in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        
        itemlist.append(create_search_item(
            title=scrapedtitle,
            search_text=scrapedtitle,
            content_type='movie',
            thumbnail=scrapedthumbnail.replace("?width=240", "?width=480"),
            year=scrapedyear,
            genre=scrapedgender
        ))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def Search(item):
    """
    Nuova ricerca globale - chiamata quando use_new_search=True
    Funzione con S maiuscola come in globalsearch.py
    """
    from specials import globalsearch
    return globalsearch.Search(item)


def new_search(item):
    """
    Vecchia ricerca - chiamata quando use_new_search=False
    """
    from specials import search as search_module
    return search_module.new_search(item)


def live(item):
    import sys
    import channelselector

    if sys.version_info[0] >= 3: from concurrent import futures
    else: from concurrent_py2 import futures

    itemlist = []
    channels_dict = {}
    channels = channelselector.filterchannels('live')

    with futures.ThreadPoolExecutor() as executor:
        itlist = [executor.submit(load_live, ch.channel) for ch in channels]
        for res in futures.as_completed(itlist):
            if res.result():
                channel_name, itlist = res.result()
                channels_dict[channel_name] = itlist

    # default order
    channel_list = ['raiplay', 'mediasetplay', 'la7', 'discoveryplus']

    # add channels not in list
    for ch in channels:
        if ch.channel not in channel_list:
            channel_list.append(ch.channel)

    # make itemlist
    for ch in channel_list:
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
