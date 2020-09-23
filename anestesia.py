import sys
import os
import re
import random
import importlib
import traceback
import asyncio
import logging as log

import discord

import config
import universal
from helpers import Scheduler

# Check if "config.LOG_FILE" folder exists and if not, try to create it.
dir_name = os.path.dirname(config.LOG_FILE)
if not os.path.exists(dir_name):
    print(f"Folder '{dir_name}' doesn't exist. Attempting to create it.")
    try:
        os.makedirs(dir_name)
    except Exception as e:
        print(f"Unfortunately, creating such a folder is nigh impossible: {e}")
        raise
    else:
        print(f'Log folder created succesfully!')

# Initialize global variables.
universal.init()


class Bot(discord.Client):
    '''Das bot.'''
    
    def load_modules(self):
        '''Load components.'''
        
        for module in config.COMPONENTS:
            try:
                exec(f'import {module}')
            except:
                log.exception('Failed to load module %s!', module)
            else:
                log.info('Module %s was loaded successfully!', module)
    
    
    def initialize_logging(self):
        '''Initialize logging.'''
        
        log.basicConfig(
            level=log.getLevelName(config.LOGGING_LEVEL),
            format="%(asctime)s [%(module)-10.10s] [%(funcName)-20.20s] [%(levelname)-8.8s]  %(message)s",
            datefmt="%d/%m/%Y %H:%M:%S",
            handlers=[
                log.FileHandler(config.LOG_FILE, encoding='utf-8'),
                log.StreamHandler()
            ]
        )
        log.getLogger("discord").setLevel(log.getLevelName(config.WRAPPER_LOGGING_LEVEL))
    
    
    async def on_ready(self):
        log.info('%s has been brought online!', client.user.name)
        self.schedules = Scheduler()
        await self.schedules.run_tasks()
                    
    
    async def on_message(self, message):
        '''React to messages.'''
        
        if message.author.name == client.user.name: 
            return
        
        words = message.content.split()
        try:
            cmd = words[0]
        except:
            return
        
        if cmd == '!pull':
            if message.author.id != int(config.OWNER): 
                return
            stream = os.popen('git pull')
            output = stream.read()
            log.info('Executed "git pull":\n%s', output)
            await message.channel.send(f'```{output}```')
        
        if cmd == '!reload':
            if message.author.id != int(config.OWNER): 
                return
            try:
                importlib.reload(config)
                log.info('config.py loaded successfully.')
            except Exception as e:
                log.exception('Failed to load config.py!')
                await message.channel.send(f':warning: Konfigurointien lataaminen epäonnistui: `{e}`')
            try:
                importlib.reload(sys.modules['helpers'])
                log.info('helpers.py loaded successfully.')
            except Exception as e:
                log.exception('Failed to load helpers.py!')
                await message.channel.send(f':warning: helpers.py-moduulin lataaminen epäonnistui: `{e}`')
            for module in config.COMPONENTS:
                try:
                    importlib.reload(sys.modules[module])
                    log.info('Component %s loaded successfully!', module)
                except KeyError:
                    try: 
                        importlib.import_module(module)
                    except:
                        log.exception('Failed to load a new component: %s', module)
                        await message.channel.send(
                        f''':warning: Juuri lisätyn komponentin `{module}` lataaminen epäonnistui:\n```python\n
                        {traceback.format_exc()}```''')
                except:
                    log.exception('Failed to load component: %s', module)
                    await message.channel.send(
                        f''':warning: Komponentin `{module}` lataaminen epäonnistui:\n```python\n
                        {traceback.format_exc()}```''')
            await message.channel.send(
                f':ok_hand::skin-tone-{random.randint(1,5)}: Komponentit ja konfiguroinnit uudelleenladattu.')
            
            self.schedules.stop()
            self.initialize_logging()
            if config.IGNORE_INTERVALS_ON_RELOAD:
                universal.first_run = True
            else:
                universal.first_run = False
            await asyncio.sleep(1)
            self.schedules = Scheduler()
            await self.schedules.run_tasks()
            
        # Not yet implemented:
        elif cmd in universal.commands:
            
            try:
                chans = config.commandPerChannels[cmd]
            except:
                chans = config.commandPerChannels['default']
            chans = chans.replace(' ', '')
            if str(message.channel.id) not in chans.split(',') and chans != '':
                return    
            
            role_id = [str(y.id) for y in message.author.roles]
            try:
                roles = config.commandPerRoles[cmd]
            except:
                roles = config.commandPerRoles['default']
            roles = roles.replace(' ', '')
            priv = False
            for r in role_id: 
                if r in roles.split(','): priv = True
            if priv is False and roles != '':
                await message.channel.send(
                    'Sinulla ei ole oikeuksia kyseiseen komentoon.')
                return
        
            mod, met = universal.commands[cmd]
            mod = importlib.import_module(mod)
            cls = getattr(mod, 'Main')
            cls = cls(message=message)
            met = getattr(cls, met)
            results = await met()
        
        else: 
            for pattern, values in universal.patterns.items():
                mod, met = values
                if re.search(pattern, message.content, flags=re.I):
                    mod = importlib.import_module(mod)
                    cls = getattr(mod, 'Main')
                    cls = cls(message=message)
                    met = getattr(cls, met)
                    results = await met()
    
    
    async def on_member_update(self, before, after):
        '''React to status changes.'''
        
        for mod, met in universal.statuses.items():
            mod = importlib.import_module(mod)
            cls = getattr(mod, 'Main')
            cls = cls(before=before, after=after)
            met = getattr(cls, met)
            results = await met()
    
universal.client = Bot()
client = universal.client
client.initialize_logging()
client.load_modules()
client.run(config.BOT_TOKEN)