import os
import re
import time
import logging as log
from datetime import datetime

import discord

import config
import universal

universal.patterns['.*']['mods.chat_log.main'] = 'message_handler'
universal.statuses['mods.chat_log.main'] = 'status_handler'

class Main:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        self.client = universal.client
        self.datefile = os.path.join(os.path.dirname(__file__), 'lastdate.txt')
        
        
    async def message_handler(self):
        self.content = str(self.message.content)
        self.chan = self.message.channel
        self.guild = self.message.guild
        servers = config.CHAT_LOG_SERVERS
        
        if self.guild.id in servers: 
            if (self.chan.id in servers[self.guild.id]['channels'] 
                or servers[self.guild.id]['channels']):
                self.server = servers[self.guild.id]
            else:
                return
        else:
            return
        
        if self.server['database']:
            await self.database_handler()
        if self.server['log_file']:
            await self.mirc_formatter()
            
   
    async def write_to_file(self, output):
        guild_name = self.guild.name
        # Remove illegal characters from server name
        invalid_chars = '<>:"/\|?* '
        for char in invalid_chars:
            guild_name = guild_name.replace(char, '')
        # Substitute user variables    
        subs = {
            '$channel_name$': self.chan.name,
            '$channel_id$': self.chan.id,
            '$server_name$': guild_name,
            '$server_id$': self.guild.id,
        }
        filename = config.CHAT_LOG_FILENAME
        for uvar, sub in subs.items():
            filename = filename.replace(uvar, str(sub))
            
        try:
            with open(filename, 'a+', encoding='utf8') as f:
                f.write(output)
        except FileNotFoundError:
            log.error("Couldn't save to %s -- check the path!", filename)
        except PermissionError:
            log.error("Couldn't save to %s -- no permissions!", filename)
                
    
    async def database_handler(self):
        pass
    
    
    async def mirc_formatter(self):
        self.role_ids = [y.id for y in self.message.author.roles]
        self.set_timestamp()
        self.set_prefix()
        self.sanitize_mentions()
        output = ''
        
        if self.date_tracker():
            output = f'Session Time: {self.mirc_date}\n'
            
        for msg in self.content.split('\n'):
            output += f"[{self.timestamp}] <{self.prefix}{self.message.author.name}> {msg}\n"
            await self.write_to_file(output)
    
    
    def set_prefix(self):
        self.prefix = config.CHAT_LOG_NICK_PREFIXES['default']
        for role, p in config.CHAT_LOG_NICK_PREFIXES.items(): 
            if role in self.role_ids:
                self.prefix = p
    
    
    def set_timestamp(self):
        self.timestamp = time.strftime("%H:%M", time.localtime())
        
        
    def sanitize_mentions(self):
        '''Convert mention id's to names.'''
        
        mentions = re.findall('<@[^0-9]?[0-9]+>', self.content)
        if not mentions:
            return
        guild = self.message.guild
        for mention in mentions:
            id = re.search('[0-9]+', mention)[0]
            name = guild.get_member(int(id)).name
            self.content = re.sub(mention, f'@{name}', self.content)
            
            
    def date_tracker(self):
        '''Date tracking for logging in mIRC format.
        This allows the bot to log the "Session Time" without being online
        at midnight and without going through the log file.'''
        
        now = datetime.now()
        self.mirc_date = datetime.strftime(now, '%a %b %d 00:00:00 %Y')
        date = datetime.strftime(now, '%d/%m/%Y')
        if not os.path.exists(self.datefile):
            with open(self.datefile, 'w') as f:
                f.write(date)
            return True
        else:
            with open(self.datefile, 'r') as f:
                prev_date = f.read()
            if prev_date == date:
                return False
            else:
                with open(self.datefile, 'w') as f:
                    f.write(date)
                return True
            
    
    async def status_handler(self):
        return
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