import re
import time
import logging as log

import discord

import config
import universal

universal.patterns['.*']['mods.chat_log.main'] = 'save_message'
universal.statuses['mods.chat_log.main'] = 'save_status_change'

class Main:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        self.client = universal.client
        
    
    def set_prefix(self):
        self.prefix = config.CHAT_LOG_NICK_PREFIXES['default']
        for role, p in config.CHAT_LOG_NICK_PREFIXES.items(): 
            if role in self.role_ids:
                self.prefix = p
    
    
    def set_timestamp(self):
        self.timestamp = time.strftime("%H:%M", time.localtime())
        
        
    def sanitize_ids(self):
        # do stuff
        pass
    
    async def save_message(self):
        self.role_ids = [str(y.id) for y in self.message.author.roles]
        self.content = str(self.message.content)
        self.set_timestamp()
        self.set_prefix()
        self.sanitize_ids()
        
        for msg in self.content.split('\n'):
            output = f"[{self.timestamp}] <{self.prefix}{self.message.author.name}> {msg}"
            print(output)
        
    
    async def save_status_change(self):
        user = str(self.after).split('#')[0]
        self.role_ids = [str(y.id) for y in self.after.roles]
        self.set_timestamp()
        self.set_prefix()     
        output = f'[{self.timestamp}] * {self.prefix}{user} ({user}@discord.com) '
        # print(self.after.status, self.before.status)
        if str(self.after.status) == 'online' and str(self.before.status) == 'offline':
            output += 'has joined #channel'
        elif str(self.after.status) == 'offline' and str(self.before.status) == 'online':
            output += 'has left #channel'
        else:
            output = False
        # print(output)

        
# mIRC-formaattireferenssi
'''
Session Time: Sat Jan 06 00:00:00 2018
[00:00] <@Allu> plaaplaa
[20:48] * Snugel (id@host) has joined #puluputes
[04:03] * @Nakke (Nakke@jakke.fi) has left #puluputes
[01:26] * @Sepe (id@host) Quit (message)
[18:21] * sipoo changes topic to 'öböbö'
'''