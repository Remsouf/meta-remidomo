#!/usr/bin/python
# -*- coding: utf-8 -*-
import pifacecommon

import pifacedigitalio

"""
Class for triggering hardware
"""
class Executor:
    RELAY_PIN = 0

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        try:
            pifacedigitalio.init()
            self.running_on_rpi = True
        except pifacecommon.spi.SPIInitError:
            self.logger.warning('Failed to init SPI. Assuming running on dev machine.')
            self.running_on_rpi = False

    def heating_poweron(self):
        self.logger.debug('Set heating ON')
        if self.running_on_rpi:
            pifacedigitalio.digital_write(self.RELAY_PIN, 1)

    def heating_poweroff(self):
        self.logger.debug('Set heating OFF')
        if self.running_on_rpi:
            pifacedigitalio.digital_write(self.RELAY_PIN, 0)
