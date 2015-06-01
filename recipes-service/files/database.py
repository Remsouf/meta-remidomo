#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Class to access the database storing our results
"""
import sqlite3

DB_PATH = '/var/remidomo/db.sqlite3'

class Database:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.connection = None

    def __connect(self):
        try:
            self.connection = sqlite3.connect(DB_PATH)
        except sqlite3.Error, e:
            self.logger.error('DB error: %s', e.args[0])
            self.connection = None

    def insert(self, device, name, value, units):
        self.logger.debug('Insert to DB: %s (%s)-> %.1f %s' % (name, device, value, units))
        self.__connect()
        self.connection.execute('INSERT INTO chauffage_mesure(name, address, timestamp, value, units) VALUES("%s", "%s", datetime("now"), %f, "%s")' % (name, device, value, units))
        self.connection.commit()
        self.__close()

    def __close(self):
        if self.connection is not None:
            self.connection.close()
