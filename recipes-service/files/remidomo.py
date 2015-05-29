#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from optparse import OptionParser
import sys
import time
import datetime

sys.path.append('/usr/lib/remidomo/service')
from executor import Executor
from rfx_listener import RFXListener
from config import Config

VERSION = '##REMIDOMO_VERSION##'

def check_orders(logger, config, executor, rfx_listener):
    # Get the schedule for today
    today = datetime.date.today().weekday()
    schedule = config.get_schedule(today)
    if schedule is None or schedule.is_empty():
        logger.info('No order for %s' % config.day_names[today])
        executor.heating_poweroff()
        return

    # Get the temperature order for now
    now = datetime.datetime.now().time()
    order = schedule.get_order_for(now)
    if order is None:
        logger.info('No order for %s @ %s' % (config.day_names[today], now.strftime('%H:%M')))
        executor.heating_poweroff()
        return

    # Execute order, depending on temperature
    sensor_name = config.get_heating_sensor_name()
    sensor_id = config.get_sensor_id(sensor_name)
    current_temperature = rfx_listener.get_sensor_value(sensor_id)
    if current_temperature is None:
        logger.info('Current temperature is not known')
        executor.heating_poweroff()
        return

    low_limit = order.get_value() - config.get_hysteresis_under()
    high_limit = order.get_value() + config.get_hysteresis_over()

    if current_temperature < low_limit:
        logger.debug('Temperature %d < %d' % (current_temperature, low_limit))
        executor.heating_poweron()
    if current_temperature > high_limit:
        logger.debug('Temperature %d > %d' % (current_temperature, high_limit))
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
    config = Config(logger)
    config.read_file(options.config)
    executor = Executor(config, logger)
    rfx_listener = RFXListener(config, logger)
    rfx_listener.start()
    while 1:
        try:
            check_orders(logger, config, executor, rfx_listener)
            time.sleep(60)
        except KeyboardInterrupt:
            print >> sys.stderr, '\nExiting by user request.\n'
            rfx_listener.stop()
            sys.exit(0)
        except Exception:
            # If main thread crashes, we must also stop RFX thread !
            rfx_listener.stop()
            raise

if __name__ == '__main__':
    main()
