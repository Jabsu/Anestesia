import logging as log
import os

import config
import universal

mod_file = 'mods.feedgasm.main'
#  + os.path.basename(__file__).split('.')[0]

n = 0
for table, settings in config.FEEDS.items():
    settings['table'] = table
    
    # Validate required settings.
    try: 
        settings['url']
    except: 
        log.error('URL not set for %s.', table)
        break
    try:
        settings['method']
    except:
        log.error('Method not set for %s.', table)
        break
    try:
        settings['channels']
    except:
        log.error('Channel(s) not set for %s.', table)
        break
    # Set defaults.
    try: 
        settings['interval']
    except: 
        settings['interval'] = 60
    try: 
        settings['image']
    except: 
        settings['image'] = 2
    try: 
        settings['spam_max']
    except: 
        settings['spam_max'] = 10
    try: 
        settings['hours']
    except: 
        settings['hours'] = False
    try: 
        settings['row_limit']
    except: 
        settings['row_limit'] = False
    try: 
        settings['color']
    except: 
        settings['color'] = False
    try: 
        settings['req_image']
    except:
        settings['req_image'] = False
    try: 
        settings['show_desc']
    except:
        settings['show_desc'] = True
    try: 
        settings['days']
    except: 
        settings['days'] = False
    n += 1
    universal.schedules[f'feed_{n}'] = [mod_file, settings]