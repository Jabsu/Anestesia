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
universal.commands['!loki'] = ('mods.chat_log.main', 'log_search')
universal.commands['!lokir'] = ('mods.chat_log.main', 'log_search_reversed')

settings = {
    'method': 'add_session_time',
    'timings': {
        'days': [],
        'times': ['00:00'],
    },
}
universal.schedules['session_time'] = ['mods.chat_log.main', settings]

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
        gid = str(self.guild.id)
        servers = config.CHAT_LOG_SERVERS
        
        if gid in servers: 
            if (str(self.chan.id) in servers[gid]['channels'] 
                or not servers[gid]['channels']):
                self.server = servers[gid]
            else:
                return
        else:
            return
        
        if self.server['database']:
            await self.database_handler()
        if self.server['log_file']:
            await self.mirc_formatter()
            
   
    async def write_to_file(self, output):
        filename = self.file_naming()
        try:
            with open(filename, 'a+', encoding='utf8') as f:
                f.write(output)
        except FileNotFoundError:
            log.error("Couldn't write to %s -- check the path!", filename)
        except PermissionError:
            log.error("Couldn't write to %s -- no permissions!", filename)
                
    
    def file_naming(self):
        guild_name = self.guild.name
        # Remove illegal characters from server name
        invalid_chars = '<>:"/\|?* '
        for char in invalid_chars:
            guild_name = guild_name.replace(char, '')
        # Substitute user variables    
        subs = {
            '$channel_name$': self.chan.name,
            '$channel_id$': str(self.chan.id),
            '$server_name$': guild_name,
            '$server_id$': str(self.guild.id),
        }
        filename = config.CHAT_LOG_FILENAME
        for uvar, sub in subs.items():
            filename = filename.replace(uvar, str(sub))
        return filename
    
    async def database_handler(self):
        pass
    
    
    async def mirc_formatter(self):
        self.role_ids = [str(y.id) for y in self.message.author.roles]
        self.set_prefix()
        self.sanitize_mentions()
        timestamp = time.strftime("%H:%M", time.localtime())
        for msg in self.content.split('\n'):
            output = f"[{timestamp}] <{self.prefix}{self.message.author.name}> {msg}\n"
            await self.write_to_file(output)
    
    
    def set_prefix(self):
        self.prefix = config.CHAT_LOG_NICK_PREFIXES['default']
        for role, p in config.CHAT_LOG_NICK_PREFIXES.items(): 
            if role in self.role_ids:
                self.prefix = p
    
    
    async def add_session_time(self, **kwargs):
        now = datetime.now()
        session_time = datetime.strftime(now, '%a %b %d 00:00:00 %Y')
        output = f'Session Time: {session_time}\n'
        
        async def write(chan, guild):
            self.chan = chan
            self.guild = guild
            await self.write_to_file(output)
        
        for server, values in config.CHAT_LOG_SERVERS.items():
            async for guild in self.client.fetch_guilds():
                if server == str(guild.id):
                    all_chans = self.client.get_all_channels()
                    if not values['channels']:
                        # All channels are logged
                        for chan in all_chans:
                            if str(chan.type) == 'text':
                                await write(chan, guild)
                    else:
                        # Specific channels are logged
                        for chan in all_chans:
                            if str(chan.id) in values['channels']:
                                if str(chan.type) == 'text':
                                    await write(chan, guild)
                            
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
            
    
    async def log_search(self, reversing=False):
        words = self.message.content.split()
        
        if len(words) < 2:
            await self.message.channel.send(
                'Hienosti! Voit myös koittaa etsiä muutakin kuin tyhjyyttä: `!loki (§nick) <regex-lauseke>`')
            return
        if words[1].startswith('§'):
            msg_pattern = '\[[0-9]+:[0-9]+\] <([0-9]+|)[^a-ö0-9]?{}([^>]+>|>) (.*)'.format(words[1].replace('§', ''))
            msg = ' '.join(words[2:])
        else:
            msg_pattern = '\[[0-9]+:[0-9]+\] <([0-9]+|)[^a-ö0-9]?([^>]+)> (.*)'
            msg = ' '.join(words[1:])
        
        filename = 'logs/testikanava.log'
        user_pattern = msg
        session_time_pattern = '^Session Time: (.*)'
        format_codes = '([0-9]+|||)'
        md_replacements = {'*': '＊', '_': '＿', '~': ''}
        date_format = '%a %b %d %H:%M:%S %Y'

        results = ''
        with open(filename, "rb") as f:
            n = 0
            session_time = 'Ennen ajanlaskun alkua'
            old_session_time = ''
            if reversing:
                lines = reversed(f.readlines())
            else:
                lines = f.readlines()
            for line in lines:
                try:
                    decoded = line.decode(encoding='utf-8')
                except UnicodeDecodeError:
                    log.error(f'!loki: Decoding error with line: {line}')
                    continue
                else:
                    match = re.search(session_time_pattern, decoded)
                    if match and not reversing:
                        session_time = match.group(1).strip()
                        session_time = datetime.strftime(datetime.strptime(session_time, date_format), '%d/%m/%Y')
                
                    decoded = re.sub(format_codes, '', decoded)
                    match = re.search(msg_pattern, decoded, re.I)
                    if match:
                        if re.search(user_pattern, match.group(3), re.I):
                            
                            if session_time != old_session_time and not reversing:
                                if len(results) + len(session_time) >= 1980: 
                                    break
                            if len(results) + len(decoded) >= 1980:
                                break
                            if not reversing:
                                results += f'> {session_time}\n'
                            old_session_time = session_time
                            n += 1
                            results += f'{n}. {decoded}'
                            if n == 10: break
                            
        if not results:
            await self.message.channel.send('Voi kun joku olisikin joskus sanonut jotain noin kaunista.')
        else:
            for char, rep in md_replacements.items():
                results = results.replace(char, rep)
            await self.message.channel.send(f'```md\n{results}```')
            
            
    async def log_search_reversed(self):
        await self.log_search(reversing=True)