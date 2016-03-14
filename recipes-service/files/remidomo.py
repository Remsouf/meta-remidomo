#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from optparse import OptionParser
import os
import sys
import time
import datetime
import sqlite3

sys.path.append('/usr/lib/remidomo/service')

from config import Config
from database import Database, TYPE_TEMP
from executor import Executor
from rfx_listener import RFXListener

VERSION = '##REMIDOMO_VERSION##'
MEASUREMENT_AGE = 60 * 30  # 30min


def check_orders(logger, config, executor, database):
    if not config.is_heating_enabled():
        return

    # Get the temperature order for now
    now = datetime.datetime.now()
    order = config.get_order_for(now)
    if order is None:
        logger.info('No order for %s @ %s' % (config.day_names[now.weekday()], now.strftime('%H:%M')))
        executor.heating_poweroff()
        return

    # Execute order, depending on temperature
    sensor_name = config.get_heating_sensor_name()
    sensor_id = config.get_temp_sensor_id(sensor_name)
    last_measure_time, current_temperature = database.query_latest(sensor_id, TYPE_TEMP)
    if current_temperature is None:
        logger.info('Current temperature is not known')
        executor.heating_poweroff()
        return

    age = datetime.datetime.now() - last_measure_time
    if age.total_seconds() > MEASUREMENT_AGE:
        logger.info('Current temperature is too old (%s), considering unreliable' % age)
        executor.heating_poweroff()
        return

    low_limit = order.get_value() - config.get_hysteresis_under()
    high_limit = order.get_value() + config.get_hysteresis_over()

    if current_temperature < low_limit:
        logger.debug('Temperature %.01f < %.01f' % (current_temperature, low_limit))
        executor.heating_poweron()
    if current_temperature > high_limit:
        logger.debug('Temperature %.01f > %.01f' % (current_temperature, high_limit))
        executor.heating_poweroff()

    # Else, no state change


def main():
    parser = OptionParser()
    parser.add_option('-o', '--output', dest='output',
                      help='write messages to FILE', metavar='FILE')
    parser.add_option('-c', '--config', dest='config',
                      help='read config from FILE', metavar='FILE')
    parser.add_option('-d', '--debug', dest='debug', action='store_true',
                      help='print debug messages')
    parser.add_option('-v', '--version', dest='version', action='store_true',
                      help='print version number and exit')
    (options, args) = parser.parse_args()

    if options.version:
        print VERSION
        sys.exit(0)

    if not options.config:
        print >> sys.stderr, 'ERROR: Please provide a config file.'
        print parser.print_help()
        sys.exit(1)

    # Logging
    logger = logging.getLogger('Remidomo')
    if options.output:
        handler = logging.FileHandler(options.output)
    else:
        handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    if options.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    # Main loop
    logger.info('Démarrage')

    config_timestamp = None
    rfx_listener = None
    while 1:
        file_timestamp = os.path.getmtime(options.config)
        if config_timestamp is None or config_timestamp != file_timestamp:
            if rfx_listener is not None:
                rfx_listener.stop()
                time.sleep(15)
            config = Config(logger)
            config.read_file(options.config)
            database = Database(config, logger)
            database.connect()
            executor = Executor(config, logger)
            rfx_listener = RFXListener(config, database, logger)
            rfx_listener.start()
            config_timestamp = file_timestamp

        try:
            check_orders(logger, config, executor, database)
            time.sleep(60)
        except KeyboardInterrupt:
            print >> sys.stderr, '\nExiting by user request.\n'
            executor.heating_poweroff()
            rfx_listener.stop()
            database.close()
            sys.exit(0)
        except Exception, e:
            logger.warning('Emergency shutdown ! %s' % e)
            executor.heating_poweroff()
            # If main thread crashes, we must also stop RFX thread !
            rfx_listener.stop()
            database.close()
            raise

if __name__ == '__main__':
    main()
