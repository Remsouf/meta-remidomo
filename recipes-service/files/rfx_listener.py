#!/usr/bin/python
# -*- coding: utf-8 -*-

from threading import Thread, RLock
import select
import socket

lock = RLock()

"""
Class to implement a thread listening to rfx-lan messages
"""
class RFXListener(Thread):
    # RFX packets are rather small...
    RECV_SIZE = 512

    # Broadcast address
    BROADCAST_IP = '255.255.255.255'

    # Select timeout
    SELECT_TIMEOUT = 10

    def __init__(self, config, logger):
        Thread.__init__(self)
        self.config = config
        self.logger = logger
        self.sensors = {}
        self.terminated = False

    def run(self):
        self.logger.debug('Starting RFX thread')
        port = self.config.get_rfxlan_port()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        addr = (self.BROADCAST_IP, port)
        try:
            sock.bind(addr)
        except:
            self.logger.error('Failed to bind !')

        self.logger.debug('Listening to RFX on %s:%d' % (self.BROADCAST_IP, port))
        while not self.terminated:
            readable, _, _ = select.select([sock], [], [], self.SELECT_TIMEOUT)
            self.logger.debug('R:%d' % len(readable))
            if len(readable) > 0:
                data, addr = sock.recvfrom(self.RECV_SIZE)
                self.logger.debug('ADDR: %s' % addr)
                self.logger.debug('DATA: %s' % data)

    def stop(self):
        self.logger.debug('Stopping RFX thread (can take up to %ds)' % self.SELECT_TIMEOUT)
        self.terminated = True
        #self._Thread__stop()

    def get_sensor_value(self, id):
        with lock:
            if id in self.sensors:
                sensor = self.sensors[id]
                return sensor.get_last_value()
            else:
                return None
