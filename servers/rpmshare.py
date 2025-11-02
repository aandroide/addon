# -*- coding: utf-8 -*-
# -*- Server RPMShare - Decriptazione AES-CBC -*-
# -*- Creato per Stream4Me -*-
# Dominio: rpmplay.xyz

"""
RPMShare Resolver - Decriptazione AES-CBC

API: /api/v1/video?id=VIDEO_ID&w=1280&h=720&r=
Risposta: Stringa HEX (non base64!), poi decriptata con AES-CBC
Decriptazione: AES-CBC con chiavi statiche

Strategia:
1. Chiama API con parametri video
2. Risposta è stringa HEX diretta
3. Converti hex in bytes
4. Decripta con AES-CBC usando chiavi statiche
5. Parsa JSON per ottenere URL video
"""

from core import httptools, scrapertools, support
from platformcode import logger, config
from six.moves import urllib_parse
import sys, json, re

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str

# Importa libreria AES (PyCrypto o PyCryptodome)
AES_AVAILABLE = False
try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    AES_AVAILABLE = True
    logger.info("Libreria AES disponibile")
except:
    try:
        from Cryptodome.Cipher import AES
        from Cryptodome.Util.Padding import unpad
        AES_AVAILABLE = True
        logger.info("Libreria AES disponibile (Cryptodome)")
    except:
        logger.info("Libreria AES NON disponibile - la decriptazione fallirà")

# Variabili globali
video_id = None
page_url_global = None
base_url = None

# Chiavi AES statiche estratte da JavaScript RPMShare
# Queste chiavi sono FISSE e funzionano per tutti i video!
RPMSHARE_KEY = 'kiemtienmua911ca'  # 16 bytes ASCII
RPMSHARE_IV = '1234567890oiuytr'   # 16 bytes ASCII


def test_video_exists(page_url):
    """Verifica se il video esiste ed estrae l'ID"""
    global video_id, page_url_global, base_url
    
    logger.info("(page_url='%s')" % page_url)
    
    # Estrai video ID dall'URL (dopo il #)
    video_id = page_url.split('#')[-1] if '#' in page_url else ''
    if video_id and '&' in video_id:
        video_id = video_id.split('&')[0]
    
    page_url_global = page_url
    parsed = urllib_parse.urlparse(page_url)
    base_url = "%s://%s" % (parsed.scheme, parsed.netloc)
    
    if not video_id or len(video_id) < 2:
        return False, config.get_localized_string(70449) % "RPMShare"
    
    logger.info("Video ID: %s" % video_id)
    return True, ""


def aes_cbc_decrypt(encrypted_hex, key, iv):
    """
    Decripta dati criptati con AES-CBC
    
    Formato RPMShare:
    - API restituisce stringa hex ASCII direttamente (NON base64!)
    - Converti hex in bytes
    - Decripta con AES-CBC
    - Rimuovi padding PKCS#7
    
    @param encrypted_hex: Stringa hex con dati criptati
    @param key: Chiave AES (stringa o bytes)
    @param iv: Vettore di inizializzazione (stringa o bytes)
    @return: Stringa decriptata
    """
    
    if not AES_AVAILABLE:
        raise Exception("Libreria AES non disponibile")
    
    # Converti stringa hex in bytes
    encrypted_hex = encrypted_hex.strip()
    
    if not re.match(r'^[0-9a-fA-F]+$', encrypted_hex):
        raise Exception("Formato non valido: attesa stringa esadecimale")
    
    if len(encrypted_hex) % 2 != 0:
        raise Exception("Lunghezza stringa hex non valida (deve essere pari)")
    
    logger.info("Stringa hex rilevata (lunghezza: %d caratteri)" % len(encrypted_hex))
    encrypted_bytes = bytes.fromhex(encrypted_hex)
    logger.info("Bytes criptati: %d bytes" % len(encrypted_bytes))
    
    # Converti chiave e IV in bytes se necessario
    if isinstance(key, str):
        key_bytes = key.encode('utf-8')
    else:
        key_bytes = key
    
    if isinstance(iv, str):
        iv_bytes = iv.encode('utf-8')
    else:
        iv_bytes = iv
    
    # Verifica che la chiave sia 16, 24 o 32 bytes (AES-128, AES-192 o AES-256)
    if len(key_bytes) not in [16, 24, 32]:
        if len(key_bytes) < 16:
            key_bytes = key_bytes.ljust(16, b'\0')
        elif len(key_bytes) < 24:
            key_bytes = key_bytes[:16]
        elif len(key_bytes) < 32:
            key_bytes = key_bytes[:24]
        else:
            key_bytes = key_bytes[:32]
    
    # Verifica che IV sia 16 bytes
    if len(iv_bytes) != 16:
        if len(iv_bytes) < 16:
            iv_bytes = iv_bytes.ljust(16, b'\0')
        else:
            iv_bytes = iv_bytes[:16]
    
    logger.info("Chiave: %d bytes, IV: %d bytes" % (len(key_bytes), len(iv_bytes)))
    
    # Decripta con AES-CBC
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
    decrypted = cipher.decrypt(encrypted_bytes)
    
    # Rimuovi padding PKCS#7
    try:
        decrypted = unpad(decrypted, AES.block_size)
    except:
        # Rimozione manuale padding PKCS#7 (fallback)
        padding_length = decrypted[-1]
        if isinstance(padding_length, str):
            padding_length = ord(padding_length)
        # Valida il padding
        if padding_length > 0 and padding_length <= AES.block_size:
            if all(b == padding_length for b in decrypted[-padding_length:]):
                decrypted = decrypted[:-padding_length]
    
    return decrypted.decode('utf-8')


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    """
    Estrae l'URL del video da RPMShare usando decriptazione AES-CBC
    """
    video_urls = []
    
    logger.info("=" * 70)
    logger.info("RPMShare Resolver (AES-CBC)")
    logger.info("Video ID: %s" % video_id)
    logger.info("=" * 70)
    
    if not AES_AVAILABLE:
        logger.error("=" * 70)
        logger.error("LIBRERIA AES NON DISPONIBILE!")
        logger.error("=" * 70)
        return video_urls
    
    # ═══════════════════════════════════════════════════════════════════════
    # Passo 1: Chiama l'API video
    # ═══════════════════════════════════════════════════════════════════════
    
    logger.info("[Passo 1] Chiamata API video...")
    
    # API con parametri
    api_url = "%s/api/v1/video?id=%s&w=1280&h=720&r=" % (base_url, video_id)
    
    try:
        api_response = httptools.downloadpage(
            api_url,
            headers={
                'Referer': page_url_global,
                'Accept': 'application/json',
            },
            alfa_s=True
        )
        
        encrypted_data = api_response.data
        logger.info("API ha restituito %d caratteri" % len(encrypted_data))
        logger.info("Sample: %s..." % encrypted_data[:50])
        
    except Exception as e:
        logger.error("Chiamata API fallita: %s" % str(e))
        return video_urls
    
    # ═══════════════════════════════════════════════════════════════════════
    # Passo 2: Decripta con AES-CBC
    # ═══════════════════════════════════════════════════════════════════════
    
    logger.info("[Passo 2] Tentativo decriptazione AES-CBC...")
    logger.info("Uso chiavi RPMShare: Key=%s, IV=%s" % (RPMSHARE_KEY, RPMSHARE_IV))
    
    try:
        decrypted = aes_cbc_decrypt(
            encrypted_data,
            RPMSHARE_KEY,
            RPMSHARE_IV
        )
        
        logger.info("Decriptazione riuscita!")
        logger.info("Dati decriptati: %s..." % decrypted[:100])
        
        # Parsa JSON
        video_data = json.loads(decrypted)
        
        # Formato RPMShare: {"status":"ok", "data":{"streams":[{"url":"..."}]}}
        video_url = None
        
        if 'data' in video_data and 'streams' in video_data['data']:
            # Formato RPMShare standard
            streams = video_data['data']['streams']
            if streams and len(streams) > 0:
                video_url = streams[0].get('url')
        elif 'url' in video_data:
            video_url = video_data['url']
        elif 'file' in video_data:
            video_url = video_data['file']
        elif 'source' in video_data:
            video_url = video_data['source']
        
        if video_url:
            logger.info("=" * 70)
            logger.info("SUCCESSO!")
            logger.info("URL Video: %s" % video_url[:80])
            logger.info("=" * 70)
            
            # Aggiungi headers necessari
            headers = {
                'User-Agent': httptools.get_user_agent(),
                'Referer': page_url_global,
                'Origin': base_url
            }
            
            url_with_headers = video_url + "|" + "&".join([
                "%s=%s" % (k, v) for k, v in headers.items()
            ])
            
            video_urls.append([" [RPMShare AES]", url_with_headers])
            return video_urls
        else:
            logger.error("URL video non trovato nel JSON decriptato")
        
    except Exception as e:
        logger.error("Decriptazione fallita: %s" % str(e))
        import traceback
        logger.error("Traceback completo:")
        logger.error(traceback.format_exc())
    
    # ═══════════════════════════════════════════════════════════════════════
    # Fallimento
    # ═══════════════════════════════════════════════════════════════════════
    
    logger.error("=" * 70)
    logger.error("DECRIPTAZIONE FALLITA")
    logger.error("=" * 70)
    logger.info("")
    logger.info("Impossibile decriptare l'URL del video")
    logger.info("")
    logger.info("Possibili motivi:")
    logger.info("1. Chiave AES/IV errata")
    logger.info("2. Algoritmo di criptazione cambiato")
    logger.info("3. Formato risposta API modificato")
    logger.info("")
    logger.info("Per risolvere:")
    logger.info("1. Apri DevTools del browser sulla pagina video")
    logger.info("2. Trova chiave AES e IV nel JavaScript")
    logger.info("3. Aggiorna RPMSHARE_KEY e RPMSHARE_IV nel resolver")
    logger.info("=" * 70)
    
    return video_urls


def get_filename(page_url):
    """Estrae il nome del file"""
    return video_id if video_id else ""