#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from optparse import OptionParser
import sys
import time

sys.path.append('/usr/lib/remidomo')
from config import Config

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
    while 1:
        config.read_file(options.config)
        logger.info('Heartbeat !')
        time.sleep(60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print >> sys.stderr, '\nExiting by user request.\n'
        sys.exit(0)

