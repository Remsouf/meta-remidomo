#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Class to access the database storing our results
"""
import MySQLdb
import time
import math
import datetime
from threading import Lock

DB_USER = 'mysql'
DB_PASSWORD = ''
DB_PORT=4321
DB_NAME = 'remidomo'
TABLE_NAME = 'remidomo_mesure'

COMPRESS = True
SAMPLING_PERIOD = 30 * 60  # 30 min
MAX_VARIATION_TEMP = 0.5  # °C
MAX_VARIATION_HUMIDITY = 10  # °H
MAX_VARIATION_POWER = 0.1  # kW

# Enum-like strings for the type column
TYPE_TEMP = 'temp'
TYPE_HUMIDITY = 'humidity'
TYPE_POWER = 'power'


class Database:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.connection = None
        self.mutex = Lock()

    def connect(self):
        try:
            self.connection = MySQLdb.connect(port=DB_PORT, user=DB_USER,
                                              passwd=DB_PASSWORD, db=DB_NAME)
        except MySQLdb.Error, e:
            self.logger.error('DB error: %s', e.args[0])
            self.connection = None

    def close(self):
        self.mutex.acquire()
        if self.connection is not None:
            self.connection.close()
            self.connection = None
        self.mutex.release()

    def check_connection(self):
        try:
            self.connection.ping(True)
            cursor = self.connection.cursor()
            cursor.execute('SELECT 1')
        except MySQLdb.OperationalError:
            self.logger.warning('Ping to DB failed, reconnecting...')
            self.connect()

    def insert(self, device, name, value, units, type):
        self.logger.debug('Save %s to DB: %s (%s)-> %.1f %s' % (type, name, device, value, units))
        self.mutex.acquire()

        self.check_connection()
        cursor = self.connection.cursor()
        if COMPRESS:
            # Get nb of values for the same sensor
            cursor.execute('SELECT COUNT(*) FROM %s WHERE name="%s" AND type="%s"' % (TABLE_NAME, name, type))
            data = cursor.fetchone()
            if data is None:
                count = 0
            else:
                count = data[0]

            now = int(time.time())

            # If not later than 30min, and below 0.5 delta,
            # just replace last value
            if count >= 2:
                cursor.execute('SELECT unix_timestamp(timestamp), value FROM %s WHERE name="%s" AND type="%s" ORDER BY timestamp DESC LIMIT 2' % (TABLE_NAME, name, type))
                data = cursor.fetchall()
                time1 = int(data[0][0])
                value1 = float(data[0][1])
                time2 = int(data[1][0])
                value2 = float(data[1][1])

                if type == TYPE_TEMP:
                    max_variation = MAX_VARIATION_TEMP
                elif type == TYPE_HUMIDITY:
                    max_variation = MAX_VARIATION_HUMIDITY
                elif type == TYPE_POWER:
                    max_variation = MAX_VARIATION_POWER
                else:
                    assert False

                if (now - time1 < SAMPLING_PERIOD) and \
                   (math.fabs(value - value1) < max_variation) and \
                   (time1 - time2 < SAMPLING_PERIOD) and \
                   (math.fabs(value1 - value2) < max_variation):
                    cursor.execute('SELECT MAX(id) FROM %s WHERE name="%s" AND type="%s"' % (TABLE_NAME, name, type))
                    data = cursor.fetchone()
                    if data is None:
                        self.logger.error('Failed to select latest value during compression')
                    else:
                        cursor.execute('DELETE FROM %s WHERE id=%d' % (TABLE_NAME, data[0]))

        # In all cases, insert the latest value
        cursor.execute('INSERT INTO %s(name, address, timestamp, value, units, type) VALUES("%s", "%s", NOW(), %f, "%s", "%s")' % (TABLE_NAME, name, device, value, units, type))
        self.connection.commit()
        self.mutex.release()

    def query_latest(self, device, type):
        self.logger.debug('Query DB for %s (%s)' % (device, type))
        self.mutex.acquire()
        self.check_connection()
        cursor = self.connection.cursor()
        cursor.execute('SELECT unix_timestamp(timestamp), value FROM %s WHERE address="%s" AND type="%s" ORDER BY timestamp DESC LIMIT 1' % (TABLE_NAME, device, type))
        data = cursor.fetchone()

        if data is None:
            result = None, None
        else:
            result = datetime.datetime.fromtimestamp(int(data[0])), float(data[1])

        self.mutex.release()
        return result

