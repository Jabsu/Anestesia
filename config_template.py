# =========================================================================================================
#                                              BOTTIASETUKSET
# =========================================================================================================

# Botin token
BOT_TOKEN = 'allutuppurainenDÖFDÖFDÖFnägNÄGKRÄÄK'

# Botin omistajan ID
OWNER = '1337'

# Komponentit
COMPONENTS = (
    'mods.feedgasm.main',
)

# Ajastetut tehtävät suoritetaan botin käynnistyksen yhteydessä intervalliasetuksista piittaamatta 
# (True/False)
IGNORE_INTERVALS_ON_LAUNCH = True

# Ajastetut tehtävät suoritetaan !reload-komentoa käytettäessä intervalliasetuksista piittaamatta 
# (True/False)
IGNORE_INTERVALS_ON_RELOAD = False

# Botin lokitustaso (mitä matalampi taso, sitä enemmän ilmoituksia)
# - TASO 1 = DEBUG
# - TASO 2 = INFO
# - TASO 3 = WARNING
# - TASO 4 = ERROR
LOGGING_LEVEL = 'DEBUG'

# API-wrapperin (discord.py) lokitustaso
WRAPPER_LOGGING_LEVEL = 'INFO'

# Tapahtumaloki
LOG_FILE = 'logs/events.log'

# Keskusteluloki (jätä tyhjäksi, jos et halua tallentaa lokia)
CHAT_LOG = '$server$-$channel$.log'

# Keskustelulokiformaatti (mirc, irssi)
CHAT_LOG_FMT = 'mirc'



# =========================================================================================================
#                                          KOMPONENTTIASETUKSET
# =========================================================================================================


# ---------------------------------------------------------------------------------------------------------
# feedgasm.py
# ---------------------------------------------------------------------------------------------------------

# SQLite-tietokannan nimi
FEEDGASM_DATABASE = 'mods/feedgasm/feedgasm.db'

# Syötekohtaiset asetukset (syötteen nimi = taulun nimi tietokannassa):

# Pakolliset:
#  - channels: spämmäyskanavat pilkulla eroteltuina
#  - url: sivu, jota *kaavitaan*
#  - method:
#    - hsc = Helsingin Sanomien sarjakuvat
#    - bbu = bigbrother.fi-sivuston uutiset
#    - rss = RSS-syötteet
#    - nel = Nelosen ohjelmakohtaiset uutiset

# Lisäasetukset:
#  - interval: tarkistusintervalli minuuteissa (default: 60)
#  - hours: tehdään tarkistus vain näinä tunteina ([0,1,2,...])
#  - days: tehdään tarkistus vain näinä päivinä ('ma','ti','ke',...)
#  - row_limit: rivien maksimimäärä tietokannassa (default: rajaton)
#  - spam_max: haettavien ja spämmättävien julkaisujen maksimimäärä per kerta (default: 10)
#  - image: upotekuva (0 = ei kuvaa, 1 = thumbnail, default: 2 = iso kuva)
#  - req_image: kuva on pakollinen (default: False)
#  - color: embedin reunan väri 0x-etuliitteisenä heksadesimaalina (default: satunnainen)
#  - show_desc: näytä kuvaus (meta description, default: True)

FEEDS = {
    'Fingerpori': {
        'channels': '531498094597111814',
        'method': 'hsc', 
        'url': 'https://www.hs.fi/fingerpori/', 
        'interval': 60, 
        'hours': [8,9,10,11,12,13],
        'days': ['ma','ti','ke','to','pe','la'],
        'color': '0x964b00',
    },
    'Big Brother': {
        'channels': '218529352617426944',
        'method': 'bbu',
        'url': 'https://www.bigbrother.fi/uutiset/',
        'interval': 10,
        'color': '0xFF1493',
    }
}


