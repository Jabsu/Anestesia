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

# Botin loggaustaso (mitä matalampi taso, sitä enemmän ilmoituksia)
# - TASO 1 = DEBUG
# - TASO 2 = INFO
# - TASO 3 = WARNING
# - TASO 4 = ERROR
LOGGING_LEVEL = 'DEBUG'

# API-wrapperin (discord.py) loggaustaso
WRAPPER_LOGGING_LEVEL = 'INFO'

# Lokitiedosto
LOG_FILE = 'logs/events.log'

# Keskustelulokitiedosto (jätä tyhjäksi, jos et halua tallentaa lokia)
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
#    - atom = ATOM-syötteet
#    - nel = Nelosen ohjelmakohtaiset uutiset
#    - rss = RSS-syötteet

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
    },
    'Anestesia': {
        'channels': '469776246750969856',
        'method': 'atom',
        'url': 'https://github.com/Jabsu/Anestesia/commits/master.atom',
        'image': 0,
        'interval': 15,
        'color': '0x2ECC71',
    }
}



# ---------------------------------------------------------------------------------------------------------
# triggers.py
# ---------------------------------------------------------------------------------------------------------

# Regex-triggeriasetukset
# 
# TRIGGERS-asetuksen rakenne: 
# {
#    'server_id_1, server_id_2': {
#        'regex_trigger_1': [
#            'tekstirivi',
#            'TOIMINTO=toiminto',
#        ],
#        'regex_trigger_2': [
#            ...    
#        ],  
#    },
#    'server_id_3, server_id_4': {
#        ...
#    },
# }
#
# Mikäli rivejä/toimintoja on useita, arvotaan näistä yksi.
#
# Toimintokytkimet:
# - FILE: satunnainen rivi tekstitiedostosta (lokaali tai URL)
# - REACT: botti reagoi emojilla (custom-emojit :aliaksella:, muutoin unicodena*)
# - EMBED: kuva/GIF
#
# * Unicode-emojin saat kirjoittamalla Discordissa \:emoji:
#
# Tekstiriveissä käytettävät muuttujat (esim. '%NICK%, olipa kauniisti sanottu'):
# - %NICK% = nimimerkki ilman mentionia
# - %MENT% = nimimerkki @mentionina
#

TRIGGERS = {
    '217544751639953409': {
        '(^|[^a-ö])tissit': [
            'REACT=♥',
            'REACT=:dolan:',
        ],
        'satunnainen sananlasku': [
            'FILE=http://hupidomain.fi/tekstitiedosto1.txt',
            'FILE=/home/nakke/txt/tekstitiedosto2.txt',
        ],
        '^<@\w+> on \w+($|\.)': [
            '%MENT%, sinä se vasta oletkin.',
        ],
        'kysymys': [
            'Onko olemassa palavaa vettä?',
            'Kuka keksi rakkauden?',
            'Muistaako kukaan sitä veristä miestä silloin Marjaniemessä?',
            'Kuka murhasi Kyllikki Saaren?',
            'Miks kaikki kaunis on niin naiivia?',
        ],
        '^nii[.!]?$': [
            'REACT=😱',
            'REACT=🙀',
            'REACT=:ohhuh:',
            'REACT=:ohhuh2:',
            'REACT=:ohhuh3:',
            'REACT=:ohhuh4:',
        ],
        '^e$': [
            'REACT=:screamy:',
            'REACT=:ohhuh:',
            'Hesus miten jäykkä.',
        ],
        '^hmm([.]+|)$': [
            'REACT=:thonk:',
            'Mitäs mietit?',
        ],
        '^!eta \w+': [
            'Soon™ :nakke:',
        ],
        '([^a-z]|^)allu([^a-z]|$)': [
            'EMBED=https://dl.dropboxusercontent.com/s/qanomnbj0jnqyxe/allu.png',
            'EMBED=https://dl.dropboxusercontent.com/s/6dfodphx99z0xb5/allu2.png',
            'EMBED=https://dl.dropboxusercontent.com/s/w4wyswl3gnksixy/allu3.png',
            'EMBED=https://dl.dropboxusercontent.com/s/xb3cmzaagw32u27/allu4.jpg',
        ],
        '(([^a-ö]|^)vit(tu|ut|un)|saatana|perkele|hele?vet|jumalaut)': [
            'REACT=🤗',
        ],
    },
}

# Embedien reunaväri (0x-alkuinen heksadesimaali, jätä tyhjäksi jos haluat satunnaisen värin)
TRIGGER_EMBED_COLOR = ''

# Botti heittäytyy kirjoitustilaan tekstuaalisten reaktioiden kohdalla
SIMULATE_HUMANS = True

# Botin kirjoitusvauhti (sekuntia per merkki)
SECS_PER_CHAR = 0.1

# Regex-rivimuokkaus käytössä 
REGSUBS = True

# Käydään läpi tämä määrä rivejä regex-muokkausta yrittäessä
REGSUBS_HISTORY_LIMIT = 100

# Ohita botin rivit
REGSUBS_SKIP_BOT = True