import os
import re
import time
import logging as log
import json
import random
from difflib import SequenceMatcher
from timeit import default_timer as timer
from datetime import datetime
from collections import OrderedDict

import discord
# from discord.utils import get

import config
import universal

universal.patterns['.*']['mods.chat_log.main'] = 'message_handler'
universal.statuses['mods.chat_log.main'] = 'status_handler'
universal.commands['!loki'] = ('mods.chat_log.main', 'log_search')
universal.commands['!lokir'] = ('mods.chat_log.main', 'log_search_reversed')

# Admin command
universal.commands['!historia'] = ('mods.chat_log.main', 'save_channel_history')

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
        if self.message.author.bot:
            return
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
        
        await self.count_words()
   
    async def write_to_file(self, output):
        filename = self.file_naming()
        try:
            with open(filename, 'a+', encoding='utf8') as f:
                f.write(output)
        except FileNotFoundError:
            log.error("Couldn't write to %s -- check the path!", filename)
        except PermissionError:
            log.error("Couldn't write to %s -- no permissions!", filename)
                
    
    def clean_illegal_chars(self, text):
        '''Remove illegal characters from a string.'''
        
        illegal_chars = '<>:"/\|?* '
        for char in illegal_chars:
            text = text.replace(char, '')
        return text
    
    
    def file_naming(self):
        guild_name = self.clean_illegal_chars(self.guild.name)
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
    
    
    async def read_userfile(self):
        file = os.path.join(os.path.dirname(__file__), 'users.json')
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                js = json.load(f)
            return js
        else:
            return {}
    
    
    async def write_to_userfile(self, data):
        file = os.path.join(os.path.dirname(__file__), 'users.json')
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, sort_keys=True, indent=4)
            
            
    async def manage_user_data(self, data, server, user, new_data):
        if not server in data:
            data[server] = {user: {}}
        if not user in data[server]: 
            data[server][user] = {}
            
        for item, value in new_data.items():
            data[server][user][item] = value
                
        await self.write_to_userfile(data)
        
        
    async def level_ups_and_roles(self, words, level):
        old_level = level
        author = self.message.author
        
        n = 0
        while True:
            level = level + 1
            n += 1
            level_up_req = eval(config.CHAT_LOG_XP_FORMULA)
            if words < level_up_req and n == 1:
                return old_level
            elif words < level_up_req:
                break
            
        level = level-1    
            
        def sub(text):
            if not text: 
                return text
            '''def num_subs(val):
                nums = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕㉖㉗㉘㉙㉚㉛㉜㉝㉞㉟㊱㊲㊳㊴㊵㊶㊷㊸㊹㊺㊻㊼㊽㊾㊿'
                # nums = [':one:', ':two:', ':three:']
                try:
                    num = nums[val-1]
                except IndexError:
                    return val
                else:
                    return num'''
                
            substitutes = {
                '$mention$': author.mention,
                '$nick$': author.name,
                '$role$': role_obj.mention,
                '$level$': str(level),
            }
            for var, sub in substitutes.items():
                text = text.replace(var, sub)
            return text
        
        if config.CHAT_LOG_TOAST_PREFIX:
            prefix = random.choice(config.CHAT_LOG_TOAST_PREFIX)
        else:
            prefix = ''
        if config.CHAT_LOG_TOAST_SUFFIX:            
            if config.CHAT_LOG_TOAST_SUFFIX == 'prefix':
                suffix = prefix
            if config.CHAT_LOG_TOAST_SUFFIX == 'random_prefix':
                suffix = random.choice(config.CHAT_LOG_TOAST_PREFIX)
        else:
            suffix = ''
        
        title = prefix + random.choice(config.CHAT_LOG_TOAST) + suffix
        old_role = self.awarded_role
        
        if str(level) in config.CHAT_LOG_AWARDS:
            if config.CHAT_LOG_TOAST_ROLE:
                desc = random.choice(config.CHAT_LOG_TOAST_ROLE)
            else:
                desc = ''
            role_id = config.CHAT_LOG_AWARDS[str(level)]
            role_obj = self.message.guild.get_role(int(role_id))
            self.awarded_role = role_obj.id
            # Give a new role
            await author.add_roles(role_obj)
            # Remove the old role
            if config.CHAT_LOG_REMOVE_OLD_ROLE and old_role:
                obj = self.message.guild.get_role(int(old_role))
                await author.remove_roles(obj)
        else:
            if not self.awarded_role:
                # Set non-awarded top role (for coloring)
                role_obj = author.roles[-1]
            else:
                # Keep the old role
                role_obj = self.message.guild.get_role(int(self.awarded_role))
            desc = ''
            
        
        
        if config.CHAT_LOG_TOAST_KUDOS:
            desc = desc + random.choice(config.CHAT_LOG_TOAST_KUDOS)
        
        if not config.CHAT_LOG_TOAST_COLOR: 
            color = int(random.random() * 16777214) + 1
        elif config.CHAT_LOG_TOAST_COLOR == 'role':
            color = role_obj.color
        else:
            color = int(self.color, 0)
        
        embed = discord.Embed(title=sub(title), url='http://foo.bar', description=sub(desc), color=color)
        if config.CHAT_LOG_TOAST_THUMBNAIL:
            embed.set_thumbnail(url=author.avatar_url)

        if self.level_up_epoch:
            date = datetime.fromtimestamp(self.level_up_epoch).strftime('%d/%m/%Y klo %H:%M')           
            embed.set_footer(text=f'Edellinen taso: {date}')
            
        self.level_up_epoch = self.epoch
            
        await self.message.channel.send(embed=embed)
        

            
        self.awarded_role = role_obj.id
            
        return level
            
        
    async def count_words(self):
        gid = str(self.guild.id)
        uid = str(self.message.author.id)
        msg = str(self.message.content).strip()
        user_data = await self.read_userfile()
        
        try:
            total_words = user_data[gid][uid]['word_count']
        except KeyError:
            total_words = 0
        try:
            prev_msg_epoch = user_data[gid][uid]['prev_msg_epoch']
        except KeyError:
            prev_msg_epoch = 0
        try:
            prev_msg = user_data[gid][uid]['prev_msg']
        except KeyError:
            prev_msg = ''
        try:
            level = user_data[gid][uid]['level']
        except KeyError:
            level = 1
        try:
            self.awarded_role = user_data[gid][uid]['awarded_role']
        except:
            self.awarded_role = 0
        try:
            self.level_up_epoch = user_data[gid][uid]['prev_lvl_up_epoch']
        except:
            self.level_up_epoch = 0
        
        self.epoch = int(time.time())
        
        stripped = re.sub('https?[^ ]+', '', msg)
        words = len(set(re.findall('[a-ö]{4,}', stripped, re.I)))
        
        # Spam precautions
        similarity = SequenceMatcher(None, prev_msg, msg).ratio()
        if self.epoch - prev_msg_epoch < 5 or similarity > 0.75:
            return
        if words > 150:
            log.debug(
                '%s wrote a message with %s unique words. Possibly spam.', self.message.author.name, words)
            return
        words = total_words + words
        
        level = await self.level_ups_and_roles(words, level)
        
        new_user_data = {
            'word_count': words,
            'prev_msg_epoch': self.epoch,
            'prev_msg': msg,
            'user_name': self.message.author.name,
            'level': level,
            'awarded_role': self.awarded_role,
            'prev_lvl_up_epoch': self.level_up_epoch,
            }
        await self.manage_user_data(user_data, gid, uid, new_user_data)
        
                
    async def mirc_formatter(self):
        self.role_ids = [str(y.id) for y in self.message.author.roles]
        self.set_prefix()
        self.sanitize_mentions()
        timestamp = time.strftime("%H:%M", time.localtime())
        name = self.clean_illegal_chars(self.message.author.name)
        for msg in self.content.split('\n'):
            output = f"[{timestamp}] <{self.prefix}{name}> {msg}\n"
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
            if mention.startswith('<@&'):
                name = guild.get_role(int(id)).name
            else:
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
            
    
    def utc_to_local(self, utc):
        '''Convert datetime from UTC to local timezone.'''
        
        epoch = time.mktime(utc.timetuple())
        offset = datetime.fromtimestamp (epoch) - datetime.utcfromtimestamp (epoch)
        return utc + offset
    

    async def save_channel_history(self):
        '''Save a channel history to a file.'''
        
        if str(self.message.author.id) != config.OWNER:
            return
        words = self.message.content.split()
        if len(words) < 2:
            self.chan = self.message.channel
        else:
            all_chans = self.client.get_all_channels()
            for ch in all_chans:
                if str(words[1]) == str(ch.id):
                    self.chan = ch
        
        self.guild = self.chan.guild
        lines = OrderedDict()
        serv_msg = await self.message.channel.send(
            f'Käydään läpi #{self.chan.name}-kanavan keskusteluhistoria. Suosittelen lenkillä käymistä tai olutta odotellessa.')
        start = timer()
        
        async for message in self.chan.history(limit=None):
            if message.author.bot:
                continue
            created_at = str(message.created_at)
            try:
                strptime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                strptime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            converted = self.utc_to_local(strptime)
            first_date = converted.strftime('%d.%m.%Y klo %H:%M')
            session_time = converted.strftime('%a %b %d 00:00:00 %Y')
            timestamp = converted.strftime('[%H:%M]')
            for l in str(message.content).splitlines():
                name = self.clean_illegal_chars(message.author.name)
                line = f'{timestamp} <{name}> {l}\n'
                try:
                    lines[session_time].append(line)
                except:
                    lines[session_time] = [line]
        
        first_msg = False
        filename = self.file_naming()
        with open(filename, "w", encoding="utf-8") as f:
            for datum, msgs in reversed(lines.items()):
                f.write(f'Session Time: {datum}\n')
                for msg in msgs:
                    if not first_msg:
                        first_msg = msg
                    f.write(msg)
        end = timer()
        seconds = int(end - start)
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        time_spent = f'{h:d} h {m:d} min {s:d} s'
        
        if not seconds:
            cnt = f'Keskusteluhistoria tallennettu onnistuneesti - ja vieläpä silmänräpäyksessä!'
        else:
            cnt = f'Keskusteluhistoria tallennettu onnistuneesti! Aikaa kesti: {time_spent}.'
        await serv_msg.edit(content=f'{cnt} Tiesitkö, että ensimmäinen viesti lähettiin {first_date}?')
        
            
    async def log_search(self, reversing=False):
        words = self.message.content.split()
        
        if len(words) < 2:
            await self.message.channel.send(
                'Hienosti! Voit myös koittaa etsiä muutakin kuin tyhjyyttä: `!loki (§nick) <regex-haku>`')
            return
        if words[1].startswith('§'):
            msg_pattern = '\[[0-9]+:[0-9]+\] <([0-9]+|)[^a-ö0-9]?{}([^>]+>|>) (.*)'.format(words[1].replace('§', ''))
            msg = ' '.join(words[2:])
        else:
            msg_pattern = '\[[0-9]+:[0-9]+\] <([0-9]+|)[^a-ö0-9]?([^>]+)> (.*)'
            msg = ' '.join(words[1:])
        self.chan = self.message.channel
        self.guild = self.message.channel.guild
        filename = self.file_naming()
        user_pattern = msg
        session_time_pattern = '^Session Time: (.*)'
        format_codes = '([0-9]+|||)'
        md_replacements = {'*': '＊', '_': '＿'}
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
                
                    decoded = re.sub(format_codes, '', decoded).strip()
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
                            results += f'{n}. {decoded}\n'
                            if n == 10: break
                            
        if not results:
            await self.message.channel.send('Voi kun joku olisikin joskus sanonut jotain noin kaunista.')
        else:
            for char, rep in md_replacements.items():
                results = results.replace(char, rep)
            await self.message.channel.send(f'```md\n{results}```')
            
            
    async def log_search_reversed(self):
        await self.log_search(reversing=True)