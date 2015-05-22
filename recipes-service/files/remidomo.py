#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from optparse import OptionParser
import sys
import time

DEFAULT_LOG_FILE = '/var/log/remidomo.log'


def main():
    parser = OptionParser()
    parser.add_option('-o', '--output', dest='output',
                      help='write messages to FILE', metavar='FILE')
    parser.add_option('-c', '--config', dest='config',
                      help='read config from FILE', metavar='FILE')
    parser.add_option('-d', '--debug', dest='debug', action='store_true',
                      help='print debug messages')
    (options, args) = parser.parse_args()
    if not options.config:
        options.config = DEFAULT_CONFIG_FILE

    # Logging
    logger = logging.getLogger('Remidomo')
    handler = logging.FileHandler(options.output or DEFAULT_LOG_FILE)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    if options.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    # Main loop
    logger.info('Démarrage')
    while 1:
        logger.info('Heartbeat !')
        time.sleep(60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print >> sys.stderr, '\nExiting by user request.\n'
        sys.exit(0)

