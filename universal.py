'''Globalisation of the, um, universe.'''

def init():
    global client, first_run, commands, patterns, timers, statuses, schedules
    try:
        client
    except:
        client = None
    else:
        if not client:
            client = None
    try:
        first_run
    except:
        first_run = True
        
    commands = {}
    # §all§ includes messages with just embeds (images, files, etc.)
    patterns = {'.*': {}, '§all§': {}}
    timers = {}
    statuses = {}
    schedules = {}