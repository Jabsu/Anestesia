# Anestesia
Suomenkielisillä toiminnallisuuksilla turboahdettu modulaarinen Discord-botti, joka hyödyntää Discord-rajapinnan käsittelyssä [discord.py](https://github.com/Rapptz/discord.py)-API-wrapperia.


## Ydintoiminnot
- Tuki ajastetuille funktioille
- Loki-ilmoitukset ja -tallennus, optionaalisesti superverbaali ulostus
- !reload-komento komponenttien ja konfigurointien uudelleenlataamista varten
- Tulossa: !avatar-komento botin profiilikuvan vaihtamista varten


## Komponentit
- *feedgasm.py*: 
    - Nuuskii Internetin syövereiden vuolaita virtoja ja poimii näistä uusimmat julkaisut halutuille kanaville
- *triggers.py*:
    - Aseta regex-triggereitä, joihin botti reagoi (satunnaisella) emojilla, kuvalla/GIF:illä tai tekstillä listasta tai tiedostosta (lokaali/url)
- *chat_log.py*: 
    - Keskustelulokitallennus mIRC-formaatissa (pisg ja mIRCStats 🖐🏼)
    - Tulossa: sanamääriin perustuvat tasot, tasokohtaiset roolitukset, regex-lokihaku jne.
- Tulossa olevat komennot ja toiminnot: 
    - Säät ja kelit käyttäjäasetuksineen
    - Välimatkat, reitit
    - Ajastin
    - Urbaani Sanakirja -haku (+ potentiaalisesti muita sanakirjahakuja)
    - Steam-haku, monipuolisemmat Steam-embedit (IsThereAnyDeal- ja DLCompare-hinnat)
    - Nukkumaanmeno- ja heräämiskomennot
    - Pakollinen kissakomento


## Asennus
1. Asenna Python 3.6+
2. Kloonaa repolainen: `git clone https://github.com/Jabsu/Anestesia.git`
3. Uudelleennimeä *config_template.py* -> *config.py* ja tee tarvittavat konfiguroinnit
4. Asenna vaaditut moduulit: `pip install -U -r requirements.txt`
5. Käynnistä botti: `python anestesia.py`