# Tehtävälista

## Botti
- ✅ Refaktorointi ja discord.py 1.0 -migraatio
- ✅ Tapahtumalokitallennus
- ✅ Päivitysnotifikaattori (feedgasm.py: ATOM-tuki)
- ✅ Ajastetut tehtävät: tuki kellonajoille


## Komponentit
- Refaktorointi ja discord.py 1.0 -migraatio
    - ✅ *helpers.py*
    - ✅ *feedgasm.py*
    - ✅ *triggers.py* (entinen jsPatterns.py)
    - ⬜ *weather.py*
    - ⬜ *embeds.py*
    - ⬜ *commands.py*
    - ⬜ *apina.py* — might just skip this 🐵
- Työn alla
    - *chat_log.py*
        - ✅ Keskustelulokitallennus mIRC-formaatissa
        - ⬜ Tietokanta
            - ⬜ Rivien tallentaminen 
            - ⬜ Ehkä: paikallaoloaikakirjanpito
        - ✅ Sanojen määrän seuraaminen
        - ✅ Sanojen määrään perustuvat tasot ilmotuksineen ja rooleineen
            - ✅ Ilmoitukset (embedinä, sisältäen käyttäjän profiilikuvan)
            - ✅ Roolitukset
        - ✅ Wiki
    - *feedgasm.py* 
        - ✅ Kanavahistoriavertailun korvaaminen SQLite-tietokannalla
        - ✅ Väriasetus
        - Kaavinta, tallennus ja ulostus
            - ✅ Helsingin Sanomien sarjakuvat
            - ✅ bigbrother.fi/uutiset
            - ✅ ATOM
            - ⬜ RSS
