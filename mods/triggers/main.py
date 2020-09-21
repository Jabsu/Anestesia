import random
import re
import asyncio
import logging as log

import chardet
import discord

import config
import universal
from helpers import Fetch

triggers = {}
universal.patterns['.*'] = ('mods.triggers.main', 'check_triggers')


class Main:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        self.client = universal.client
        self.content = str(self.message.content)
        self.nick = str(self.message.author).split('#')[0]
    
    
    async def switches(self):
        if self.switch == 'FILE':
            if 'http' in self.value:
                fetch = Fetch(url=self.value) 
                file = await fetch.request()
                r = random.choice(file.splitlines())
                enc = chardet.detect(r)['encoding']
                try:
                    result = r.decode(enc)
                except:
                    log.exception('Something went wrong with decoding the file %s!', self.value)
                    result = None
                
            else:
                r = random.choice(open(self.value).read().splitlines())
                if type(r) is not str:
                    enc = chardet.detect(r)['encoding']
                    result = r.decode(enc)
                else:
                    result = r
        elif self.switch == 'REACT':
            if ':' not in self.value: return self.value
            result = self.value
            for e in self.client.emojis:
                if str(e).split(':')[1] == self.value.split(':')[1]: result = e
        
        elif self.switch == 'EMBED':
            result = ''
                    
        return result
        
    
    async def create_embed(self):
        if not config.TRIGGER_EMBED_COLOR: 
            color = int(random.random() * 16777214) + 1
        else:
            try:
                color = int(self.color, 0)
            except:
                log.error('Incorrect hexadecimal for trigger embed color: %s.')
                color = int(random.random() * 16777214) + 1
        
        embed = discord.Embed(color=color)
        embed.set_image(url=self.value)
        await self.message.channel.send(embed=embed)
        
    
    async def convert_emoji(self, line):
        self.orig_msg = line
        try:
            customEmoji = re.search('(:[^:]+:)', line, flags=re.I).group(0)
            for e in self.client.get_all_emojis():
                if str(e).split(':')[1] == customEmoji.replace(':', ''): 
                    return(line.replace(customEmoji, str(e)))
        except:
            return self.orig_msg
        return self.orig_msg
        
   
    async def regex_substitute(self):
        if self.regsub.group(4) != 'g': count = 1
        else: count = 0
        if self.regsub.group(4) == 'i': flag = 're.I'
        else: flag = 0
        
        
        async for message in self.message.channel.history(limit=config.REGSUBS_HISTORY_LIMIT):
            if message.content == self.message.content: continue
            if config.REGSUBS_SKIP_BOT and message.author == self.client.user: continue
            if re.search(self.regsub.group(2), message.content, flags=flag):
                self.msg = f'<{str(message.author.name)}> ' + re.sub(self.regsub.group(2), self.regsub.group(3), message.content, count, flags=flag)
                # if config.REGEX_IMAGE: await self.make_image() 
                # else: await self.client.send_message(self.message.channel, self.msg)
                await self.message.channel.send(self.msg)
                break
            
    
    async def make_image(self):
        '''Not yet implemented.'''
        
        selected_font = 'consola.ttf'
        original_font_size = 16
        bg = (54, 57, 63)
        fg = (214, 215, 217)
        font = ImageFont.truetype(selected_font, original_font_size)
        font_size = font.getsize(self.msg)
        img = Image.new('RGB', (font_size[0], original_font_size), color = bg)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(selected_font, original_font_size)
        draw.text((0,0), self.msg, fg, font)
        img.save('temp.png')
        await self.client.send_file(self.message.channel, 'temp.png')
    
    
    async def check_triggers(self):
        
        keys = []
        for server, triggers in config.TRIGGERS.items():
            if str(self.message.guild.id) in server.replace(' ', '').split(','):
                keys.append(server)
                continue
                
        if not keys: return
        
        if config.REGSUBS:
            self.regsub = re.search(r'^s([^a-z ])(.*?)\1(.*?)\1([ig]?)', self.content)
            if self.regsub: 
                await self.regex_substitute()
                return
        
        for key in keys:
            for regex, values in config.TRIGGERS[key].items():
                try:
                    match = re.search(regex, self.content, flags=re.I)
                except Exception as e:
                    log.error('Regex-syntaksisi on virheellinen: %s', e)
                    match = False
                if match:
                    line = random.choice(values)
                    try: 
                        self.switch, self.value = line.split('=')
                        value = await self.switches()
                        if self.switch == 'REACT':
                            await self.message.add_reaction(value)
                            return
                        elif self.switch == 'EMBED':
                            await self.create_embed()
                            return
                        else: 
                            message = await self.convert_emoji(value)                        
                    except ValueError:
                        message = await self.convert_emoji(line)
                    except:
                        log.exception('Something quite peculiar just happened!')
                        return
                        
                    msg = self.orig_msg.replace('%NICK%', self.nick).replace('%MENT%', self.nick)
                
                    if config.SIMULATE_HUMANS:
                        type_delay = round(len(msg) * config.SECS_PER_CHAR,2)
                        async with self.message.channel.typing():
                            await asyncio.sleep(type_delay)
                            await self.message.channel.send(message.replace('%NICK%', self.nick).replace('%MENT%', self.message.author.mention))
                    else:
                        await self.message.channel.send(message.replace('%NICK%', self.nick).replace('%MENT%', self.message.author.mention))    
                
    
                