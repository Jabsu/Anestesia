import os
import sys
import re
import time
import logging as log
import json
import random
import importlib
import textwrap
import asyncio
from difflib import SequenceMatcher
from timeit import default_timer as timer
from datetime import datetime
from collections import OrderedDict

import discord
# from discord.utils import get

import config
import universal
from helpers import Database

universal.patterns['§all§']['mods.chat_log.main'] = 'message_handler'
universal.statuses['mods.chat_log.main'] = 'status_handler'

# Commands
this = 'mods.chat_log.main'
universal.commands['!loki'] = (this, 'log_search')
universal.commands['!lokir'] = (this, 'log_search_reversed')
universal.commands['!taso'] = (this, 'show_my_level')
universal.commands['!tasot'] = (this, 'show_top_list')

# Admin commands
universal.commands['!historia'] = (this, 'save_channel_history')

settings = {
    'method': 'add_session_time',
    'timings': {
        'days': [],
        'times': ['00:00'],
    },
}
universal.schedules['session_time'] = ['mods.chat_log.main', settings]

locked_channel = 0

class Main:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        global locked
        self.client = universal.client
        self.datefile = os.path.join(os.path.dirname(__file__), 'lastdate.txt')
        self.loop = asyncio.get_event_loop()
        self.tasks = []
        
    async def message_handler(self):
        
        if self.message.author.bot:
            return
        if self.message.channel.id == locked_channel:
            return
        self.content = str(self.message.clean_content)
        self.chan = self.message.channel
        self.guild = self.message.guild
        gid = str(self.guild.id)
        servers = config.CHAT_LOG_SERVERS
        
        if gid in servers: 
            if (str(self.chan.id) in servers[gid]['channels'] 
                or not servers[gid]['channels']):
                self.server = servers[gid]
                self.config_classes(gid)
            else:
                return
        else:
            return
        
        if self.server['database']:
            await self.database_handler()
        if self.server['log_file']:
            await self.mirc_formatter()
        
        await self.count_words(message=self.message)
        
        
    async def show_my_level(self):
        user_data = await self.read_userfile()
        gid = str(self.message.guild.id)
        if not user_data:
            await self.message.channel.send('Ei olemassa olevia käyttäjätietoja.')
            return
        try:
            user_data[gid]
        except KeyError:
            await self.message.channel.send('Tällä serverillä ei ole käyttäjätietoja.')
            return
        
        uid = str(self.message.author.id)
        cid = str(self.message.channel.id)
        self.guild = self.message.guild
        self.chan = self.message.channel
        
        self.config_classes(gid)
        
        try:
            level = user_data[gid][uid]['level']
        except KeyError:
            await self.message.channel.send('Sano ensin jotain.')
            return
        words = user_data[gid][uid]['word_count']
        lvl_up = user_data[gid][uid]['prev_lvl_up_epoch']
        if lvl_up:
            date = datetime.fromtimestamp(user_data[gid][uid]['prev_lvl_up_epoch']).strftime('%d/%m/%Y')
        db = DatabaseHandling(client=self.client, db=self.file_naming('db'))
        sql = f"SELECT created_at, jump_url FROM '{cid}' WHERE author_id IS '{uid}' ORDER BY created_at ASC LIMIT 1"
        try:
            first_msg, jump_url = db.retrieve(sql)[0]
        except IndexError:
            first_msg = False
        db.close()
        if first_msg: 
            try:
                first_msg = datetime.strptime(first_msg, '%Y-%m-%d %H:%M:%S').strftime('%d/%m%/Y')
            except ValueError:
                first_msg = datetime.strptime(first_msg, '%Y-%m-%d %H:%M:%S.%f').strftime('%d/%m/%Y')
        
        role = self.message.author.roles[-1]
        try:
            color = role.color
        except:
            color = None
        
        embed = discord.Embed(title=self.message.author.name, color=color)
        embed.add_field(name='Sanojen määrä', value='{:,}'.format(words).replace(',', ' '))
        if lvl_up:
            embed.add_field(name='Taso saavutettu', value=date)
        color_hex = str(color).replace('#', '')
        embed.set_thumbnail(url=f'https://dummyimage.com/100x100/2F3136/{color_hex}.png&text={level}')
        
        if self.server_config.CHAT_LOG_LEVELS_JUMP_URLS and first_msg:
            value = f'[{first_msg}]({jump_url})'
        elif first_msg:
            value = first_msg 
        if first_msg:
            embed.add_field(name='Ensimmäinen viesti', value=value)
        
        await self.message.channel.send(embed=embed)
        
        
    async def show_top_list(self):
        gid = str(self.message.guild.id)
        cid = str(self.message.channel.id)
        if len(self.message.content.split()) > 1:
            cid = str(self.message.content.split()[1])
        user_data = await self.read_userfile()
        self.guild = self.message.guild
        self.chan = self.message.channel
        if not user_data:
            await self.message.channel.send('Ei olemassa olevia käyttäjätietoja.')
            return
        try:
            user_data[gid]
        except KeyError:
            await self.message.channel.send('Tällä serverillä ei ole käyttäjätietoja.')
            return
        
        self.config_classes(gid)
        embed = discord.Embed(title='Vuolaimmat keskustelijat')
        placement = 1
        sql = "SELECT created_at, jump_url FROM '{}' WHERE author_id IS '{}' ORDER BY created_at ASC LIMIT 1"
        db = DatabaseHandling(client=self.client, db=self.file_naming('db'))
        ordered = OrderedDict()
        for user, values in user_data[gid].items():
            lvl = values['level']
            ordered[lvl] = values
            ordered[lvl]['user'] = user
        
        for level, values in reversed(sorted(ordered.items())):
            if placement > self.server_config.CHAT_LOG_TOP:
                break
            level = values['level']
            word_count = values['word_count']
            if placement == 1:
                suffix = ' \👑'
            else:
                suffix = ''
                
            if values['user_name'] == 'Deleted User':
                user = '*poistettu käyttäjä*'
            else:
                user = values['user_name']
            embed.add_field(name=f'Taso **{level}**{suffix}', value=user, inline=True)
            try:
                first_msg, jump_url = db.retrieve(sql.format(cid, values['user']))[0]
            except IndexError:
                first_msg = False
            else:
                try:
                    first_msg = datetime.strptime(first_msg, '%Y-%m-%d %H:%M:%S').strftime('%d/%m%/Y')
                except ValueError:
                    first_msg = datetime.strptime(first_msg, '%Y-%m-%d %H:%M:%S.%f').strftime('%d/%m/%Y')
                if self.server_config.CHAT_LOG_LEVELS_JUMP_URLS and first_msg:
                    value = f'[{first_msg}]({jump_url})'
                elif first_msg:
                    value = first_msg 
            if not first_msg:
                value = 'ei tietoa'
            embed.add_field(name='Ensimmäinen viesti', value=value, inline=True)
            embed.add_field(name='\u200B', value='\u200B', inline=True)
            
            placement += 1
            
        db.close()
            
        embed.set_thumbnail(url=self.guild.icon_url)
        await self.chan.send(embed=embed)
    
    
    def config_classes(self, guild_id):
        '''Set server specific configurations.'''
        cls_name = config.CHAT_LOG_SERVERS[guild_id]['class']
        self.server_config = getattr(config, cls_name)()
        
        
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
    
    
    def file_naming(self, output='text'):
        guild_name = self.clean_illegal_chars(self.guild.name)
        # Substitute user variables    
        subs = {
            '$channel_name$': self.chan.name,
            '$channel_id$': str(self.chan.id),
            '$server_name$': guild_name,
            '$server_id$': str(self.guild.id),
        }
        if output == 'text':
            filename = config.CHAT_LOG_FILENAME
        else:
            filename = config.CHAT_LOG_DATABASE
        for uvar, sub in subs.items():
            filename = filename.replace(uvar, str(sub))
        return filename
    
    
    async def database_handler(self):
        db = DatabaseHandling(client=self.client, db=self.file_naming('db'))
        db.insert_message(message=self.message, table=self.message.channel.id)
        db.close()
    
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
        
        
    async def level_ups_and_roles(self, words, level, retrospective, message):
        old_level = level
        author = message.author
        
        n = 0
        while True:
            level = level + 1
            n += 1
            level_up_req = eval(self.server_config.CHAT_LOG_XP_FORMULA)
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
        
        if self.server_config.CHAT_LOG_TOAST_PREFIX:
            prefix = random.choice(self.server_config.CHAT_LOG_TOAST_PREFIX)
        else:
            prefix = ''
        if self.server_config.CHAT_LOG_TOAST_SUFFIX:            
            if self.server_config.CHAT_LOG_TOAST_SUFFIX == 'prefix':
                suffix = prefix
            if self.server_config.CHAT_LOG_TOAST_SUFFIX == 'random_prefix':
                suffix = random.choice(self.server_config.CHAT_LOG_TOAST_PREFIX)
        else:
            suffix = ''
        
        title = prefix + random.choice(self.server_config.CHAT_LOG_TOAST) + suffix
        old_role = self.awarded_role
        
        if str(level) in self.server_config.CHAT_LOG_AWARDS:
            if self.server_config.CHAT_LOG_TOAST_ROLE:
                desc = random.choice(self.server_config.CHAT_LOG_TOAST_ROLE)
            else:
                desc = ''
            role_id = self.server_config.CHAT_LOG_AWARDS[str(level)]
            role_obj = message.guild.get_role(int(role_id))
            self.awarded_role = role_obj.id
            # Give a new role
            if retrospective:
                try:
                    user = await message.guild.fetch_member(author.id)
                except discord.errors.NotFound:
                    user = None
                except Exception as e:
                    log.debug('Fetching member %s resulted with an error: %s', author.name, e)
                    user = None
            else: 
                user = author
            
            if user:
                try:
                    await user.add_roles(role_obj)
                except:
                    log.error("I wasn't able to add a role to user %s", author.name)
                # Remove the old role
                if self.server_config.CHAT_LOG_REMOVE_OLD_ROLE and old_role:
                    obj = message.guild.get_role(int(old_role))
                    try:
                        await user.remove_roles(obj)
                    except:
                        log.error("I wasn't able to remove a role from user %s", author.name)
        else:
            if not self.awarded_role:
                # Set non-awarded top role (for coloring)
                role_obj = author.roles[-1]
            else:
                # Keep the old role
                role_obj = message.guild.get_role(int(self.awarded_role))
            desc = ''
            
        
        
        if self.server_config.CHAT_LOG_TOAST_KUDOS:
            desc = desc + random.choice(self.server_config.CHAT_LOG_TOAST_KUDOS)
        
        if not self.server_config.CHAT_LOG_TOAST_COLOR: 
            color = int(random.random() * 16777214) + 1
        elif self.server_config.CHAT_LOG_TOAST_COLOR == 'role':
            color = role_obj.color
        else:
            color = int(self.color, 0)
        
        embed = discord.Embed(title=sub(title), url='http://foo.bar', description=sub(desc), color=color)
        if self.server_config.CHAT_LOG_TOAST_THUMBNAIL:
            embed.set_thumbnail(url=author.avatar_url)

        if self.level_up_epoch:
            date = datetime.fromtimestamp(self.level_up_epoch).strftime('%d/%m/%Y klo %H:%M')           
            embed.set_footer(text=f'Edellinen taso: {date}')
            
        self.level_up_epoch = self.epoch
            
        if self.server_config.CHAT_LOG_LEVELING_SPAM and not retrospective:
            if not self.server_config.CHAT_LOG_LEVELING_CHAN: 
                await message.channel.send(embed=embed)
            else:
                chan = self.client.get_channel(int(self.server_config.CHAT_LOG_LEVELING_CHAN))
                if chan:
                    await chan.send(embed=embed)
                else:
                    log.error("I wasn't able to send a level up message to the channel you have set.")
                    
            
        self.awarded_role = role_obj.id
            
        return level
            
        
    async def count_words(self, retrospective=False, message=''):
        gid = str(self.guild.id)
        uid = str(message.author.id)
        msg = str(message.content).strip()
        user_data = await self.read_userfile()
        # self.config_classes(gid)
        
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
            if not retrospective:
                return
        if words > 150 and not retrospective:
            log.debug(
                '%s wrote a message with %s unique words. Possibly spam.', message.author.name, words)
            return
        words = total_words + words
        
        level = await self.level_ups_and_roles(words, level, retrospective, message)
        
        new_user_data = {
            'word_count': words,
            'prev_msg_epoch': self.epoch,
            'prev_msg': msg,
            'user_name': message.author.name,
            'level': level,
            'awarded_role': self.awarded_role,
            'prev_lvl_up_epoch': self.level_up_epoch,
            }
        await self.manage_user_data(user_data, gid, uid, new_user_data)
        
                
    async def mirc_formatter(self):
        self.role_ids = [str(y.id) for y in self.message.author.roles]
        self.set_prefix()
        # self.sanitize_mentions()
        timestamp = time.strftime("%H:%M", time.localtime())
        name = self.clean_illegal_chars(self.message.author.name)
        if self.message.content:
            for msg in self.content.split('\n'):
                output = f"[{timestamp}] <{self.prefix}{name}> {msg}\n"
                await self.write_to_file(output)
        elif self.message.attachments:
            for att in self.message.attachments:
                output = f"[{timestamp}] <{self.prefix}{name}> {att.url}\n"
                await self.write_to_file(output)
    
    
    def set_prefix(self):
        self.prefix = self.server_config.CHAT_LOG_NICK_PREFIXES['default']
        for role, p in self.server_config.CHAT_LOG_NICK_PREFIXES.items(): 
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
            name = False
            id = re.search('[0-9]+', mention)[0]
            if mention.startswith('<@&'):
                name = guild.get_role(int(id))
            elif mention.startswith('<@!'):
                name = guild.get_member(int(id))
            if name:
                self.content = re.sub(mention, f'@{name.name}', self.content)

    
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
    

    async def progress_updater(self):
        msg_template = 'Käydään läpi #{}-kanavan keskusteluhistoria... {}'
        name = self.chan.name
        text = ''
        self.serv_msg = await self.message.channel.send(msg_template.format(name, text))
        while self.snooping:
            if self.total_msgs:
                total_msgs = '{:,}'.format(self.total_msgs).replace(',', ' ')
                text = f'**{total_msgs}** riviä käsitelty.'
            msg = msg_template.format(name, text)
            try:
                await self.serv_msg.edit(content=msg)
            except Exception as e:
                log.debug('An exception during progress_updater: %s', e)
            await asyncio.sleep(1)
            
        
    async def save_channel_history(self):
        '''Save a channel history to a file.'''
        
        if str(self.message.author.id) != config.OWNER:
            return
        
        global locked_channel
        
        words = self.message.content.split()
        if len(words) < 2:
            self.chan = self.message.channel
        else:
            all_chans = self.client.get_all_channels()
            for ch in all_chans:
                if str(words[1]) == str(ch.id):
                    self.chan = ch
        
        self.guild = self.chan.guild
        self.config_classes(str(self.guild.id))
        lines = OrderedDict()
        start = timer()
        
        save_to = self.server_config.CHAT_LOG_HISTORY_SAVED_TO
        
        if save_to == 'both' or save_to == 'db':
            db_name = config.CHAT_LOG_DATABASE
            db = DatabaseHandling(client=self.client, db=self.file_naming('db'))
            db.drop_table(str(self.message.channel.id))
        
        self.total_msgs = 0
        old_date = 0
        first_msg = False

        def convert_time(created_at):
            try:
                strptime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                strptime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            converted = self.utc_to_local(strptime)
            return converted
        
        # Disable normal channel logging until history is saved
        locked_channel = self.message.channel.id
        
        # Start progress updater
        self.snooping = True
        self.tasks.append(self.loop.create_task((self.progress_updater())))
        
        async for message in self.chan.history(limit=None):
            if message.author.bot:
                continue
            if save_to == 'both' or save_to == 'db':
                db.insert_message(message=message, table=message.channel.id)
                
            if message.clean_content:
                converted = convert_time(str(message.created_at))
                timestamp = converted.strftime(f'[\[%H:%M\]]({message.jump_url})')
                msg = f'{timestamp} <{message.author.name}> {message.clean_content}'.replace("`", "'")
                if old_date != converted:
                    first_msg = False
                    old_date = converted
                if not first_msg:
                    first_date = converted.strftime('%d.%m.%Y')
                    first_msg = textwrap.shorten(msg, width=200, placeholder='…')
                    
            
            if message.clean_content and self.server_config.CHAT_LOG_RETROSPECTIVE_LEVELING:
                # Retrospective leveling
                await self.count_words(retrospective=True, message=message)
                
            if save_to == 'text' or save_to == 'both':
                # mIRC log formatting
                converted = convert_time(str(message.created_at))
                # first_date = converted.strftime('%d.%m.%Y klo %H:%M')
                session_time = converted.strftime('%a %b %d 00:00:00 %Y')
                timestamp = converted.strftime('[%H:%M]')
                for l in str(message.clean_content).splitlines():
                    name = self.clean_illegal_chars(message.author.name)
                    line = f'{timestamp} <{name}> {l}\n'
                    try:
                        lines[session_time].append(line)
                    except:
                        lines[session_time] = [line]
                        
            self.total_msgs += 1
        
        self.snooping = False
        for task in self.tasks:
            task.cancel
        self.tasks = []
        
        if save_to == 'db' or save_to == 'both':
            db.close()
        
        if save_to == 'text' or save_to == 'both':
            filename = self.file_naming()
            with open(filename, "w", encoding="utf-8") as f:
                for datum, msgs in reversed(lines.items()):
                    f.write(f'Session Time: {datum}\n')
                    for msg in reversed(msgs):
                        f.write(msg)
        
        end = timer()
        seconds = int(end - start)
        
        if seconds:
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            time_spent = f'{h:d} h {m:d} min {s:d} s'
        else:
            time_spent = 'silmänräpäys'
        locked_channel = 0
        total_msgs = '{:,}'.format(self.total_msgs).replace(',', ' ')
        
        title = f'Kanavan #{self.chan.name} keskusteluhistoria tallennettu onnistuneesti!'
        
        user = await message.guild.fetch_member(self.client.user.id)
        color = user.roles[-1].color
        embed = discord.Embed(color=color)
        embed.add_field(name='Aikaa kesti', value=time_spent, inline=True)
        embed.add_field(name='Viestejä yhteensä', value=total_msgs, inline=True)
        embed.add_field(name=f'Ensimmäinen viesti ({first_date})', value=first_msg, inline=False)
        
        await self.serv_msg.delete()
        await self.message.channel.send(content=title, embed=embed)
        
            
    async def log_search(self, reversing=False):
        words = self.message.content.split()
        
        if len(words) < 2:
            await self.message.channel.send(
                'Hienosti! Voit myös koittaa etsiä muutakin kuin tyhjyyttä: `!loki (§nick) <regex-haku>`')
            return
        if words[1].startswith('§'):
            user = words[1].replace('§', '')
            msg_pattern = f'\[[0-9]+:[0-9]+\] <([0-9]+|)[^a-ö0-9]?{user}([^>]+>|>) (.*)'
            msg = ' '.join(words[2:])
        else:
            user = None
            msg_pattern = '\[[0-9]+:[0-9]+\] <([0-9]+|)[^a-ö0-9]?([^>]+)> (.*)'
            msg = ' '.join(words[1:])
        
        self.chan = self.message.channel
        self.guild = self.message.channel.guild
        
        self.config_classes(str(self.guild.id))
        if self.server_config.CHAT_LOG_SEARCH_METHOD == 'db':
            if reversing:
                sort_order = 'DESC'
            else:
                sort_order = 'ASC'
            await self.db_log_search(msg, user, sort_order)
        else:
            await self.mirc_log_search(msg, msg_pattern)
            
            
    async def db_log_search(self, regex, user, sort_order):
        cid = str(self.message.channel.id)
        db = DatabaseHandling(client=self.client, db=self.file_naming('db'), regex_function=True)
        # limit = 10
        
        if user:
            sql = f'''
            SELECT clean_content as C, author_name as U, created_at, jump_url FROM '{cid}' 
            WHERE U IS ? COLLATE NOCASE AND lower(C) REGEXP ? ORDER BY created_at {sort_order}'''
            ret = db.retrieve(sql, [user, regex])
        else:
            sql = f'''
            SELECT clean_content as C, author_name, created_at, jump_url FROM '{cid}' 
            WHERE lower(C) REGEXP ? ORDER BY created_at {sort_order}'''
            ret = db.retrieve(sql, [regex])
        
        db.close()
        
        if ret and type(ret) is list:
            
            total_lines = len(ret)
            line_count = 0
            lines = ''
            if sort_order == 'ASC':
                suffix = 'vanhimmasta uusimpaan'
            else:
                suffix = 'uusimmasta vanhimpaan'
            
            for values in ret:
                msg, author, date, url = values
                msg = textwrap.shorten(msg, width=200, placeholder='…').replace('`', "'")
                try:
                    strptime = datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    strptime = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                date = datetime.strftime(self.utc_to_local(strptime), '[%d/%m/%y]')
                line = f'[{date}]({url}) <**{author}**> {msg}\n'
                if len(lines+line) >= 2020: 
                    break
                else:
                    lines += line
                    line_count += 1
                
            embed = discord.Embed(title=f'Hakutulokset ({line_count}/{total_lines}) {suffix}', description=lines)
            await self.chan.send(embed=embed)
        
        elif type(ret) is str:
            await self.chan.send('Pahoittelen, mutta tällä kanavalla on liian synkkä historia.')
        else:
            await self.chan.send('Voi kun joku olisikin joskus sanonut jotain noin kaunista.')

    async def mirc_log_search(self, msg, msg_pattern):
        filename = self.file_naming()
        user_pattern = msg
        session_time_pattern = '^Session Time: (.*)'
        format_codes = '([0-9]+|||)'
        md_replacements = {'*': '＊', '_': '＿', '`': "'"}
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
        
        

class DatabaseHandling(Main):
    
    def __init__(self, client=None, db=None, regex_function=False):
        if client:
            self.client = client
        self.db = Database(db=db)
        self.columns = {
            'author': 'TEXT',
            'author.id': 'TEXT',
            'author.name': 'TEXT',
            'author.nick': 'TEXT',
            'clean_content': 'TEXT',
            'channel.name': 'TEXT', 
            'message_id': 'TEXT',
            'attachment_urls': 'TEXT',
            'pinned': 'TEXT',
            'reactions': 'TEXT',
            'raw_mentions': 'TEXT',
            'raw_channel_mentions': 'TEXT',
            'raw_role_mentions': 'TEXT',
            'created_at': 'TEXT',
            'edited_at': 'TEXT',
            'jump_url': 'TEXT',
        }
        self.db_name = db
        if regex_function:
            self.db.conn.create_function('REGEXP', 2, self.regexp)
    
    
    def regexp(self, expr, item):
        reg = re.compile(expr.lower())
        return reg.search(item) is not None            
    
    
    def drop_table(self, table):
        log.info("%s: Dropping table (if exists) %s.", self.db_name, table)
        sql = f'DROP TABLE if exists "{table}"'
        self.db.alter(sql)
        
    
    def create_table(self, table):
        log.info("%s: Attempting to create table %s.", self.db_name, table)
        columns = 'id INTEGER PRIMARY KEY'
        for col, datatype in self.columns.items():
            columns += f', {col} {datatype}'
        sql = f'CREATE TABLE if not exists "{table}" ({columns})'.replace('.', '_')
        self.db.alter(sql)
        
        
    def insert_message(self, message=None, table=None):
        code = "INSERT INTO '{}' ({}) VALUES ({})"
        columns = ', '.join([c for c in self.columns])
        question_marks = ','.join('?' * len(self.columns))
        values = []
        for col, datatype in self.columns.items():
            if col == 'message_id': 
                val = message.id
            elif col == 'attachment_urls':
                attachments = message.attachments
                val = []
                if attachments:
                    for attachment in attachments:
                        val.append(attachment.url)
                    val = ','.join(val)
                else:
                    val = None
            elif '.' in col:
                c = col.split('.')
                val = getattr(message, c[0])
                try:
                    val = str(getattr(val, c[1]))
                except:
                    val = None
            else:
                if col == 'created_at' or col == 'edited_at' and getattr(message, col):
                    # Convert datetime
                    try:
                        strptime = datetime.strptime(str(getattr(message, col)), '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        strptime = datetime.strptime(str(getattr(message, col)), '%Y-%m-%d %H:%M:%S')
                    val = Main.utc_to_local('this.selfie', strptime)
                else: 
                    val = str(getattr(message, col))
            
            values.append(val)
        
        code = code.format(table, columns, question_marks).replace('.', '_')
        ret = self.db.alter(code, values)
        
        if ret:
            if 'no such table' in ret:
                self.create_table(table)
                ret = self.db.alter(code, values)
            elif 'has no column named' in ret:
                while ret:
                    column = re.search('column named (.*)', ret)[1]
                    col_type = self.columns[column]
                    sql = f"ALTER TABLE '{table}' ADD COLUMN {column} {col_type}"
                    log.info('Altering the table by adding the missing column.')
                    ret = self.db.alter(sql)
                    
                    
    def retrieve(self, sql, params=None):
        return (self.db.retrieve(sql, params))
    
    
    def close(self):
        self.db.close()
