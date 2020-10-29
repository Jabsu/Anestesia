import sqlite3
import logging as log
import time
import re
from datetime import datetime

import discord

from helpers import Database
import universal
import config

class DatabaseHandling:
    
    def __init__(self, client=None):
        if client:
            self.client = client
        self.db = Database(db=config.CHAT_LOG_DATABASE)
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

        
    def create_table(self, table):
        log.info("%s: Attempting to create table '%s'.", config.CHAT_LOG_DATABASE, table)
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
                    val = self.utc_to_local(strptime)
                else: 
                    val = str(getattr(message, col))
            
            values.append(val)
        
        code = code.format(table, columns, question_marks).replace('.', '_')
        ret = self.db.alter(code, values)
        
        if ret:
            if 'no such table' in ret:
                self.create_table(table)
                ret = self.db.alter(code, values)
            if 'has no column named' in ret:
                while ret:
                    column = re.search('column named (.*)', ret)[1]
                    col_type = self.columns[column]
                    sql = f"ALTER TABLE '{table}' ADD COLUMN {column} {col_type}"
                    log.info('Altering the table by adding the missing column.')
                    ret = self.db.alter(sql)
                    
    
    def utc_to_local(self, utc):
        '''Convert datetime from UTC to local timezone.'''
        epoch = time.mktime(utc.timetuple())
        offset = datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)
        return utc + offset
    
    
    def close(self):
        self.db.close()
        
        
    
        
        
