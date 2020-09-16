import logging as log
from helpers import Database
import config

class DatabaseHandling:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.db_name = config.FEEDGASM_DATABASE
        self.session = Database(db=self.db_name)
    
    def create_table(self):
        
        log.info("%s: Creating table %s.", self.db_name, self.table)
        columns = 'id INTEGER PRIMARY KEY'
        for col, datatype in self.sql_columns.items():
            columns += f', {col} {datatype}'
        sql = f'CREATE TABLE if not exists "{self.table}" ({columns});'''
        self.session.alter(sql)
        
        if self.row_limit:
            self.create_row_trigger()
        
    def create_row_trigger(self):
        log.debug('%s: Row limit set to %d, creating trigger.', self.db_name, self.row_limit)
        sql = f"""CREATE TRIGGER row_limit
                  AFTER INSERT ON '{self.table}'
                  BEGIN
                  DELETE FROM '{self.table}' WHERE id <= (
                      SELECT id FROM '{self.table}' 
                      ORDER BY id 
                      DESC LIMIT {str(self.row_limit)}, 1);
                  END;
               """
        self.session.alter(sql)
        

    def insert(self):
        sql_insert = "INSERT INTO '{}' ({}) VALUES ({})"
        columns = ''
        for c in self.sql_columns:
            columns += f'{c}, '
        
        for n, cols in self.publications.items():
            values = ''
            for data in cols.values():
                values += f'"{data}", '
            sql = sql_insert.format(self.table, columns.rstrip(', '), values.rstrip(', '))
            self.session.alter(sql)
        
    def iterate_columns(self):

        sql_select = "SELECT {0} FROM '{1}' WHERE {0} = '{2}'"
        pubs = self.publications.copy()
        
        for key, columns in pubs.items():
            sql = sql_select.format(self.comparison_item, self.table, columns[self.comparison_item])
            ret = self.session.retrieve(sql)
            if ret:
                if 'no such table' in ret:
                    self.create_table()
                else:
                    # Item already in database.
                    self.publications.pop(key)
        
        # Insert new items, if any.
        if self.publications:
            self.insert()
        
        self.session.close()
        return self.publications
                
    