import sqlite3 
import asyncio
import aiohttp
import requests
import importlib
import logging as log
from datetime import datetime

from bs4 import BeautifulSoup as bs

import config
import universal


class Database:
    '''A class for SQLite related stuff.'''
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.conn = sqlite3.connect(self.db)
    
    
    def alter(self, code, params=None):
        ret = self.execute(code, params)
        if not ret:
            try:
                self.conn.commit()
            except sqlite3.OperationalError as e:
                log.error('%s: SQLite error: %s', self.db, e)
                
        return ret
        
    
    def retrieve(self, code, params=None):
        ret = self.execute(code, params)
        if not ret: 
            ret = self.cur.fetchall()
        return ret 
    
    
    def execute(self, code, params=None):
        self.cur = self.conn.cursor()
        try:
            if params:
                self.cur.execute(code, params)
            else:
                self.cur.execute(code)
        except sqlite3.OperationalError as e:
            log.error('%s: SQLite error: %s', self.db, e)
            return f'SQLite error: {str(e)}'
        else:
            return None
        
    
    def close(self):
        self.conn.close()


class Fetch:
    '''Requesting and cooking http data.'''
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        # set defaults
        try:
            self.cookies
        except:
            self.jar = ''
        else:
            self.set_cookies()
        try:
            self.headers
        except:
            self.headers = {}
        try: 
            self.allow_redirects
        except:
            self.allow_redirects = True
        
        self.content = None
        
      
    async def cook(self, **kwargs):
        try:
            parser
        except:
            parser = 'html.parser'
        if self.content:
            return bs(self.content, parser)
    
    
    def set_cookies(self):
        self.jar = requests.cookies.RequestsCookieJar()
        for n, cookies in self.cookies:
            self.jar.set(cookies)

    
    async def request(self):
        
        try:
            self.verify_ssl
        except:
            self.session = aiohttp.ClientSession(cookies=self.jar)
            
        else:
            self.session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(verify_ssl=False), 
                cookies=self.jar)
        
        try:
            async with self.session.get(
                self.url, headers=self.headers, 
                allow_redirects=self.allow_redirects) as self.r:
        
                if self.r.status == 200:
                    # log.debug('%s -- the request went fine!', self.url)
                    self.content = await self.r.read()
                    await self.session.close()
                    return self.content
                elif self.r.status == 404:
                    await self.session.close()
                    log.error("%s: not found (404) :(", self.url)
                else:
                    log.error("%s: %s :(", self.url, self.r.status)
                    await self.session.close()
        except:
            log.exception('A http request resulted with an exception!')
                

class Scheduler:
    '''A custom scheduler, or: a stubborn effort to reinvent the wheel (e.g. discord.ext.tasks).'''
    
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.tasks = []
        self.client = universal.client
    
    
    async def log_exceptions(self, awaitable):
        try:
            return await awaitable
        except Exception:
            log.exception("An unhandled exception just happened with a scheduled task!")
        
    
    async def interval_loop(self, met, args):
        while True:
            if universal.first_run and config.IGNORE_INTERVALS_ON_LAUNCH: 
                await asyncio.sleep(1)
            elif universal.first_run and config.IGNORE_INTERVALS_ON_LAUNCH:
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(args['interval']*60)

            if len(args) > 2: 
               await met(**args)
            else: 
                await met()
            if universal.first_run:
                universal.first_run = False
                
                
    async def timed_loop(self, met, args):
        timings = args['timings']
        while True:
            await asyncio.sleep(1)
            now = datetime.now()
            day = datetime.strftime(now, '%a')
            time = datetime.strftime(now, '%H:%M')
            passes = 0
            def check(val, val_name):
                if not timings[val_name]: 
                    return True
                else:
                    for v in timings[val_name]:
                        if v == val:
                           return True
            if check(day, 'days'):
                passes += 1
            if check(time, 'times'):
                passes += 1
            if passes == 2:
                await met(**args)
                await asyncio.sleep(60)
                
    async def run_tasks(self):
        for e, l in universal.schedules.items():
            mod, args = l
            mod = importlib.import_module(mod)
            cls = getattr(mod, 'Main')
            cls = cls()
            met = getattr(cls, args['method'])
            try:
                args['timings']
            except:
                self.tasks.append(self.loop.create_task(self.log_exceptions(self.interval_loop(met, args))))
            else:
                self.tasks.append(self.loop.create_task(self.log_exceptions(self.timed_loop(met, args))))
            
            log.debug('A new scheduled task was created: %s', str(met))
        

    def stop(self):
        for task in self.tasks:
            task.cancel()
        self.tasks = []
