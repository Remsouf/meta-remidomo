#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Class to access the database storing our results
"""
import sqlite3
import time
import math
import datetime

DB_PATH = '/var/remidomo/db.sqlite3'
TABLE_NAME = 'chauffage_mesure'

COMPRESS = True
SAMPLING_PERIOD = 30*60  # 30 min
MAX_VARIATION = 0.5  # °C


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
        self.logger.debug('Save to DB: %s (%s)-> %.1f %s' % (name, device, value, units))
        self.__connect()

        if COMPRESS:
            # Get nb of values for the same sensor
            cursor = self.connection.cursor()
            cursor.execute('SELECT COUNT(*) FROM %s WHERE name="%s"' % (TABLE_NAME, name))
            data = cursor.fetchone()
            if data is None:
                count = 0
            else:
                count = data[0]

            now = int(time.time())

            # If not later than 30min, and below 0.5 delta,
            # just replace last value
            if count >= 2:
                cursor.execute('SELECT strftime("%%s", timestamp), value FROM %s WHERE name="%s" ORDER BY timestamp DESC LIMIT 2' % (TABLE_NAME, name))
                data = cursor.fetchall()
                time1 = int(data[0][0])
                value1 = float(data[0][1])
                time2 = int(data[1][0])
                value2 = float(data[1][1])

                if ((now-time1 < SAMPLING_PERIOD) and
                    (math.fabs(value - value1) < MAX_VARIATION) and
                    (time1 - time2 < SAMPLING_PERIOD) and
                    (math.fabs(value1 - value2) < MAX_VARIATION)):
                    self.connection.execute('DELETE FROM %s WHERE name="%s" AND id=(SELECT MAX(id) FROM %s WHERE name="%s")' % (TABLE_NAME, name, TABLE_NAME, name))

        # In all cases, insert the latest value
        self.connection.execute('INSERT INTO %s(name, address, timestamp, value, units) VALUES("%s", "%s", datetime("now"), %f, "%s")' % (TABLE_NAME, name, device, value, units))
        self.connection.commit()
        self.__close()

    def query_latest(self, device):
        self.logger.debug('Query DB for %s' % device)
        self.__connect()
        cursor = self.connection.cursor()
        cursor.execute('SELECT strftime("%%s", timestamp), value FROM %s WHERE address="%s" ORDER BY timestamp DESC LIMIT 1' % (TABLE_NAME, device))
        data = cursor.fetchone()

        if data is None:
            return None, None
        else:
            return datetime.datetime.fromtimestamp(int(data[0])), float(data[1])

    def __close(self):
        if self.connection is not None:
            self.connection.close()
