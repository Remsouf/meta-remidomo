#!/usr/bin/python
# -*- coding: utf-8 -*-
import pifacecommon
import pifacedigitalio
import time

class Executor:
    """
    Class for triggering hardware
    """
    SERVICE_PIN = 7
    RELAY_PIN = 0
    SENSOR_PIN = 5
    ACTIVITY_PIN = 4
    BLINK_TIME = 0.5  # seconds

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        try:
            pifacedigitalio.init()
            self.running_on_rpi = True
        except pifacecommon.spi.SPIInitError:
            self.logger.warning('Failed to init SPI. Assuming running on dev machine.')
            self.running_on_rpi = False
        except pifacedigitalio.core.NoPiFaceDigitalDetectedError:
            self.logger.warning('PifaceDigital not present.')
            self.running_on_rpi = False

    def heating_poweron(self):
        self.logger.debug('Set heating ON')
        if self.running_on_rpi:
            pifacedigitalio.digital_write(self.RELAY_PIN, 1)

    def heating_poweroff(self):
        self.logger.debug('Set heating OFF')
        if self.running_on_rpi:
            pifacedigitalio.digital_write(self.RELAY_PIN, 0)

    def blink_sensor(self):
        self.logger.debug('Blink sensor LED')
        if self.running_on_rpi:
            pifacedigitalio.digital_write(self.SENSOR_PIN, 1)
            time.sleep(self.BLINK_TIME)
            pifacedigitalio.digital_write(self.SENSOR_PIN, 0)

    def blink_activity(self):
        self.logger.debug('Blink activity LED')
        if self.running_on_rpi:
            pifacedigitalio.digital_write(self.ACTIVITY_PIN, 1)
            time.sleep(self.BLINK_TIME)
            pifacedigitalio.digital_write(self.ACTIVITY_PIN, 0)

    def service_flag(self, enabled):
        self.logger.debug('Set service LED %d' % enabled)
        if self.running_on_rpi:
            pifacedigitalio.digital_write(self.SERVICE_PIN, enabled)

