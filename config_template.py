# =========================================================================================================
#                                              BOTTIASETUKSET
# =========================================================================================================

# Botin token
BOT_TOKEN = 'nekottob'

# Botin omistajan ID
OWNER = '1337'

# Komponentit
COMPONENTS = (
    'mods.feedgasm.main',
    'mods.triggers.main',
    'mods.chat_log.main',
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

# Komentojen kanavakohtaiset käyttöoikeudet
CMD_CHANNEL_PRIVILEGES = {
	'!apina': '399506424406736896, 218529352617426944',
    'default': '217576842654121984, 218529352617426944, 531498094597111814',
}

# Komentojen roolikohtaiset käyttöoikeudet
CMD_ROLE_PRIVILEGES = {
	'default': '217546906765623296',
}




# =========================================================================================================
#                                          KOMPONENTTIASETUKSET
# =========================================================================================================



# ---------------------------------------------------------------------------------------------------------
# chat_log.py
# ---------------------------------------------------------------------------------------------------------

# Serverit, joiden keskustelut logataan tietokantaan ja/tai tekstitiedostoon
CHAT_LOG_SERVERS = {
    '217544751639953409': {
        'database': True, # tietokantatallennus (hyödyllinen regex-lokihauissa)
        'log_file': True, # tiedostotallennus (mIRC-lokiformaatissa)
        'channels': ['217576842654121984', '218529352617426944', '399506424406736896'], # logattavat kanavat ([] = kaikki kanavat)
        'class': 'ChatLogServerA', # serverikohtaisten asetusten luokka (nimi ei saa sisältää erikoismerkkejä tai välilyöntejä)
    },
}

# Lokitiedoston sijainti ja nimirakenne
# Tuetut muuttujat: $server_id$, $server_name$, $channel_id$, $channel_name$
CHAT_LOG_FILENAME = 'logs/$server_name$_#$channel_name$.log'

# SQLite-tietokannan sijainti ja nimirakenne
# Tuetut muuttujat: $server_id$, $server_name$
CHAT_LOG_DATABASE = 'mods/chat_log/$server_name$.db'

# Oletusasetukset (nämä voi ylikirjoittaa serverikohtaisissa asetusluokissa)
# Huomaathan, että sisennykset ovat välilyöntejä
class ChatLogDefaults:
    
    def __init__(self):
        
        # Kanavan keskusteluhistoria (!historia-komennolla) tallennetaan
        # 'db' = vain tietokantaan
        # 'text' = vain tekstiedostoon (mIRC-lokiformaatissa)
        # 'both' = molempiin
        self.CHAT_LOG_HISTORY_SAVED_TO = 'both'
        
        # Lokihaku (!loki) tietokannasta (db) tai tekstitiedostosta (text)
        self.CHAT_LOG_SEARCH_METHOD = 'db'
        
        # Tasoilmoitukset käytössä
        self.CHAT_LOG_LEVELING_SPAM = True
        
        # Linkki ensimmäiseen viestiin !taso- ja !tasot-komennoissa
        self.CHAT_LOG_LEVELS_JUMP_URLS = True
        
        # Top-listan maksimi
        self.CHAT_LOG_TOP = 5

        # Tasot nousevat retrospektiivisesti, kun kanavan keskusteluhistoria tallennetaan komennolla
        # (Tyhjennä users.json-tiedostossa serverikohtainen sisältö ("server_id": {}) tai poista koko tiedosto ennen tätä, mikäli 
        # tämä on jo generoitu, muuten sanojen laskenta ei ala alusta)
        self.CHAT_LOG_RETROSPECTIVE_LEVELING = True
        
        # Laskukaava vaadittavien sanojen määrälle per taso
        self.CHAT_LOG_XP_FORMULA = '250 * (level ** 2) - (250 * level)'

        # Poistetaanko edellinen tasokohtainen rooli, kun saavutetaan uusi?
        self.CHAT_LOG_REMOVE_OLD_ROLE = True

        # Embedin otsikko
        self.CHAT_LOG_TOAST = [
            '**$nick$** on saavuttanut tason **$level$** ',
            '**$nick$** kipusi ihan noin vaan tasolle **$level$** ',
            '**$nick$** loikkasi tasolle **$level$** ',
            '**$nick$** saavutti tason **$level$** ',
            '**$nick$** singahti tasolle **$level$** ',
            '**$nick$** puhui itsensä tasolle **$level$** ',
        ]

        # Otsikon etuliite (jätä tyhjäksi, jos et halua etuliitettä)
        # Escapeta (\) emoji, jos haluat, ettei Discord korvaa sitä omalla versiollaan
        self.CHAT_LOG_TOAST_PREFIX = [
            '\🤗 ',
            '\❤️ ',
            '\💚 ', 
            '\💜 ',
            '\🧡 ',
            '\💙 ',
            '\🤍 ',
            '\🤎 ', 
            '\💗 ', 
            '\💖 ',
        ]

        # Otsikon jälkiliite (jätä tyhjäksi, jos et halua jälkiliitettä)
        #  'prefix': sama kuin etuliite
        #  'random_prefix': sama kuin etuliite, mutta uudestaan arvottuna
        #  [uusi_lista]
        self.CHAT_LOG_TOAST_SUFFIX = 'prefix'

        # Onnittelua edeltävä teksti, jos uusi rooli saavutettu
        self.CHAT_LOG_TOAST_ROLE = [
            'Mitäs porukka on mieltä? Eikös $nick$ ansaitse roolin $role$?\n\n',
            'Tästä hyvästä hänen roolikseen on nyt määritetty $role$!\n\n',
            '$nick$, rooliksesi on aktiivisuutesi ansiosta määritetty $role$!\n\n',
            'Aktiivisuus kannattaa: $nick$ sai roolin $role$!\n\n',
            'Kyllä kannatti höpötellä, $nick$: rooliksesi on määritetty $role$!\n\n',
        ]

        # Onnittelut
        self.CHAT_LOG_TOAST_KUDOS = [
            'Sanoisin, että onnittelut ovat paikallaan. Onnittelut!',
            'Onnittelut ~~perheenlisäyksestä~~ huikeasta saavutuksesta!',
            'Onnittelut ~~ripille pääsystä~~ ihan käsittämättömän hienosta saavutuksesta!',
            'Onnittelut ~~syntymäpäivän johdosta~~ vahvasta suorituksesta!',
            'Onnitella kannattaa, kun onniteltavaa on. Onnitteluni siis.',
            'Lasten mehuhetki päättyi ikävästi, mutta $nick$ hymyilee varsin leveästi. Onnea!',
            'Suosiiko onni rohkeaa? Onko $nick$ rohkea? Tarvittiinko tähän onnea? Onnea!',
            'Ihan käsittämätöntä, miten hienosti jotkut onnistuvat pyrkimyksissään. Onnea!',
            'Kelpaa onnitella, kun tunteella ja taidolla tehdään tällaisia valtavan hienoja saavutuksia.'
        ]

        # Onnittelu-embedin reunaväri
        #  'role' = (viimeksi) saavutetun roolin väri
        #  '0xHEX' = asetettu väri
        #  '' = satunnainen väri
        self.CHAT_LOG_TOAST_COLOR = 'role'

        # Käyttäjän thumbnail onnittelu-embedissä
        self.CHAT_LOG_TOAST_THUMBNAIL = True

# Serverikohtainen asetusluokka
class ChatLogServerA(ChatLogDefaults): # 1. pakollinen rivi
    # ^^^^^^^^^^^^^^ luokan nimi, johon viitataan CHAT_LOG_SERVERS-asetuksessa
    def __init__(self):                # 2. pakollinen rivi 
    
        ChatLogDefaults.__init__(self) # 3. pakollinen rivi
       
        # Roolikohtaiset nimimerkki-prefixit (mIRC-lokitallennusta varten):
        self.CHAT_LOG_NICK_PREFIXES = {
            '217546906765623296': '@',
            '217577600493682689': '+',
            'default': '',
        }
        
        # Tasokohtaiset roolit
        self.CHAT_LOG_AWARDS = {
            '2': '770359140110958632', # 500 sanaa, jos käytössä oletuslaskukaava
            '5': '770359752336080906', # 5 000 sanaa
            '10': '770360163067625512', # 22 500 sanaa
            '20': '770361085370433536', # 95 000 sanaa
        }

        # Tasoilmoituskanava ('' = ilmoitus tulee sille kanavalle, missä viesti on lähetetty)
        self.CHAT_LOG_LEVELING_CHAN = ''


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
#        'regex_trigger_1': [ # Mikäli rivejä/toimintoja on useita, arvotaan näistä yksi
#            'tekstirivi',
#            'TOIMINTO=toiminto',
#        ],
#        'regex_trigger_2': [
#            ...    
#        ],  
#    },
#    'server_id_1, server_id_3': { # Sama serveri voi olla tarvittaessa useassa eri triggerinipussa
#        ...
#    },
# }
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

# Käydään läpi tämä määrä viimeisimpiä rivejä regex-muokkausta yrittäessä
REGSUBS_HISTORY_LIMIT = 100

# Ohitetaan botin omat rivit regex-muokkausta yrittäessä
REGSUBS_SKIP_BOT = True