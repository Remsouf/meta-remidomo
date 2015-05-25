#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Class for triggering hardware
"""
class Executor:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def heating_poweron(self):
        self.logger.debug('Set heating ON')

    def heating_poweroff(self):
        self.logger.debug('Set heating OFF')
