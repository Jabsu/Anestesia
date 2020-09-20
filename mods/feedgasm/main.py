import os 
import sys
import time
import random
import importlib
import datetime as dt
import re 
import logging as log

import discord

from helpers import Fetch
import config
import universal

from . import set_defaults
from .db_handling import DatabaseHandling

importlib.reload(sys.modules['mods.feedgasm.set_defaults'])

class Main():
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.client = universal.client
        self.sql_columns = {
            'title': 'TEXT', 
            'desc': 'TEXT', 
            'url': 'TEXT', 
            'image_url': 'TEXT', 
            'footer': 'TEXT',
        }
        self.publications = {}

      
    def valid_hours(self):
        ret = True
        if universal.first_run:
            return True
        if self.hours:
            try: hour = int(time.strftime('%H').lstrip('0'))
            except: hour = False
            if not hour: hour = 0
            if hour not in self.hours: ret = False
        if self.days:
            repl = {'su': 0, 'ma': 1, 'ti': 2, 'ke': 3, 'to': 4, 'pe': 5, 'la': 6}
            days = []
            for d in self.days:
                try: days.append(d.replace(d, str(repl[d])))
                except: pass
            if time.strftime('%w') not in days: 
                ret = False
        return ret
        
    
    async def db_operations(self):
        db = DatabaseHandling(
            publications=self.publications, comparison_item=self.comparison_item, sql_columns=self.sql_columns,
            table=self.table, row_limit=self.row_limit)
        self.publications = db.iterate_columns()
        
    
    async def make_soup(self, url=None):
        if not url:
            url = self.url
        fetch = Fetch(url=url)
        await fetch.request()
        soup = await fetch.cook()
        return soup
        
    
    async def spam_to_channels(self):
        for chan in self.channels.replace(' ', '').split(','):
            self.channel = self.client.get_channel(int(chan))
            if not self.channel:
                log.error('No such channel: %s', chan)
                continue
            else:
                await self.spam()
                
    
    async def spam(self):
        for n in reversed(range(1,self.item_count+1)):
            try:
                item = self.publications[n]
            except:
                continue
                
            if self.show_desc and item['desc']: 
                desc = item['desc']
            else:
                desc = False
            embed = discord.Embed(
                title=item['title'], description=desc, url=item['url'], color=self.color)
            if item['image_url']:
                if self.image == 2: 
                    embed.set_image(url=item['image_url'])
                elif self.image == 1: 
                    embed.set_thumbnail(url=item['image_url'])
            if item['footer']: 
                embed.set_footer(text=item['footer'])
            await self.channel.send(embed=embed)
            
            
    def init_scraper(self, **kwargs):
        '''Common stuff for scrapers.'''
        
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        if not self.valid_hours(): 
            return False
        
        try:
            self.comparison_item
        except:
            self.comparison_item = 'url'
        
        self.publications = {}
        self.item_count = 1
        
        if not self.color: 
            self.color = int(random.random() * 16777214) + 1
        else:
            self.color = int(self.color, 0)
        
        return True
        
        
    async def scraping_done(self):
        await self.db_operations()
        if self.publications: 
            await self.spam_to_channels()
    
        
    async def hsc(self, **kwargs):
        '''Helsingin Sanomat's comics scraper.'''
        
        if not self.init_scraper(**kwargs):
            return
        
        log.debug('Requesting %s', self.url)
        soup = await self.make_soup()
        items = soup.find_all('li', class_='list-item cartoon')
       
        if not items: 
            log.warning("%s: Couldn't find any comics. Has the page source changed?", self.table)
            return
        
        
        
        for item in items:
            try:
                footer = item.find('span', class_='date').text.strip()
            except:
                footer = False
            self.publications[self.item_count] = {
                'title': item.find('span', class_='title').text.strip(),
                'desc': None,
                'url': 'https://www.hs.fi' + item.find('a').get('href'),
                'image_url': 'https:' + item.find('img').get('data-srcset').split(' ')[0],
                'footer': footer,
            }
            
            if self.item_count == int(self.spam_max): 
                break
            self.item_count += 1
            
        await self.scraping_done()

        
    async def bbu(self, **kwargs):
        '''Big Brother news scraper.'''
        
        if not self.init_scraper(**kwargs):
            return
        
        log.debug('%s: Requesting %s', self.table, self.url)
        soup = await self.make_soup()
        items = soup.find_all('article')
                
        if not items: 
            log.warning("%s: Couldn't find any articles. Has the page source changed?", self.table)
            return
        
        for item in items:
            href = 'https://www.bigbrother.fi' + item.find('a').get('href')
            soup = await self.make_soup(url=href)
            
            try:
                title = soup.find('meta', property='og:title').get('content')
                # title = title.replace('"', "”")
            except:
                log.warning('No title found for %s', href)
                title = 'Ei otsikkoa'
            try:
                desc = soup.find('meta', property='og:description').get('content')
                # desc = desc.replace('"', "”")
            except:
                desc = False
            try:
                image_url = soup.find('meta', property='og:image').get('content')
            except:
                image_url = False
            try:
                footer = soup.find(
                    'div', id='___gatsby').find('main').find('div', color='greys.base').text
            except:
                footer = None
                
            self.publications[self.item_count] = {
                'title': title,
                'desc': desc,
                'url': href,
                'image_url': image_url,
                'footer': footer,
            }
            
            if self.item_count == int(self.spam_max): 
                break
            self.item_count += 1
            
        await self.scraping_done()
        
        
    async def atom(self, **kwargs):
        '''ATOM feed scraper.'''
        
        if not self.init_scraper(**kwargs):
            return
        
        self.parser = 'lxml-xml'
        log.debug('Requesting %s', self.url)
        soup = await self.make_soup()
        entries = soup.find_all('entry')
        
        if not entries:
            log.warning("%s: Couldn't find any entries. Please validate the ATOM feed.", self.table)
            return

        for entry in entries:
            try:
                title = entry.find('title').text.strip()
            except:
                log.debug('Unable to retrieve <title> from an entry. Skipping.')
                continue
            try:
                url = entry.find('link').get('href')
            except:
                log.debug('Unable to retrieve <link> from an entry. Skipping.')
                continue
            try:
                updated = entry.find('updated').text
                strptime = dt.datetime.strptime(updated, '%Y-%m-%dT%H:%M:%SZ')
                footer = strptime.strftime('%d/%m/%Y klo %H:%M')
            except:
                footer = False
            try:
                content = entry.find('content').text.strip()
                desc = re.search('<pre.*?\n\n(.*)', content, re.DOTALL).group(1)
                desc = desc.replace('</pre>', '')
            except:
                desc = False
            try:
                image_url = entry.find('media:thumbnail').get('url')
            except:
                image_url = False
       
            self.publications[self.item_count] = {
                'title': title,
                'desc': desc,
                'url': url,
                'image_url': image_url,
                'footer': footer,
            }
            
            if self.item_count == int(self.spam_max): 
                break
            self.item_count += 1
            
        await self.scraping_done()
                
            
            
    async def rss(self, **kwargs):
        '''RSS feed scraper -- not yet implemented/refactored.'''
        return
        
        if not self.init_scraper(**kwargs):
            return
        
        log.debug('Requesting %s', self.url)
        self.parser = 'lxml-xml'
        soup = await self.make_soup()
        
        items = soup.find_all('entry')
        
        # Reddit specific RSS feed scraper:
        if 'reddit.com' in self.url:
            self.parser = 'html.parser'
            for item in self.soup.find_all('entry'):
                
                link = item.find('link').get('href')
                try: title = item.find('title').text
                except: title = 'No title'
                self.url = link
                
                await self.cook()
                desc = False
                try: 
                    if self.showDesc: desc = self.soup.find('meta', property='og:description').get('content')
                except: 
                    pass
                try: img = self.soup.find('meta', property='og:image').get('content')
                except Exception as e: 
                    if self.reqImage: continue
                    else: img = False
                publ[self.item_count] = {'link': link, 'title': title, 'desc': desc, 'img': img}
                self.publications[self.item_count] = {'link': link, 'title': title, 'desc': desc, 'img': img}
                if self.item_count == int(self.loadspam): break
                self.item_count += 1
                
            
        else:
            for item in self.soup.find('channel').find_all('item'): 
                title = item.find('title').text.strip()
                link = item.find('link').text
                try: desc = item.find('description').text.strip()
                except: desc = False
                try: 
                    img = item.find('media:content').get('url')
                except: 
                    if self.reqImage: continue
                    else: img = False
                publ[self.item_count] = {'link': link, 'title': title, 'desc': desc, 'img': img}
                self.publications[self.item_count] = {'link': link, 'title': title, 'desc': desc, 'img': img}
                if self.item_count == int(self.loadspam): break
                self.item_count += 1
            
        
        
        for chan in self.channels.replace(' ', '').split(','):
            self.channel = self.client.get_channel(chan)
            await self.compare()
            if self.publications: await self.spam()
            self.publications = publ
            

    async def NEL(self, **kwargs):
        '''Nelonen's news scraper. Refactoring needed.'''
        
        log.info('Nelonen news scraper not yet implemented.')
        return
        
        for key, value in kwargs.items():
            setattr(self, key, value)
        if not self.valid_hours(): return
        self.method = 'NEL'
        self.parser = 'html.parser'
        await self.cook()
        publ = {}
        self.publications = {}
        self.item_count = 1
        for item in self.soup.find_all('article', class_='node node-story node-promoted'):
            title = item.find('a').text.strip()
            try: img = item.find('img').get('src')
            except: img = False
            link = 'https://www.nelonen.fi' + item.find('a').get('href')
            try: desc = item.find('div', {'class': re.compile(r'field field-name-body.*')}).find('p').text
            except: desc = False
            publ[self.item_count] = {'link': link, 'title': title, 'desc': desc, 'img': img}
            self.publications[self.item_count] = {'link': link, 'title': title, 'desc': desc, 'img': img}
            if self.item_count == int(self.loadspam): break
            self.item_count += 1
        
        for chan in self.channels.replace(' ', '').split(','):
            self.channel = self.client.get_channel(chan)
            await self.compare()
            if self.publications: await self.spam()
            self.publications = publ
        
    
    async def TWT(self, **kwargs):
        '''Twitter scraper placeholder.'''
        
        return