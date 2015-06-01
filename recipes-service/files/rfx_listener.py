#!/usr/bin/python
# -*- coding: utf-8 -*-

from threading import Thread, RLock
import select
import socket
from database import Database
from xpl_msg import xPLMessage

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
        self.database = None
        self.terminated = False

    def run(self):
        self.logger.debug('Starting RFX thread')

        # This separate thread needs its own DB connection
        self.database = Database(self.config, self.logger)

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
            if len(readable) > 0:
                data, _ = sock.recvfrom(self.RECV_SIZE)
                msg = xPLMessage(data)
                self.handle_message(msg)

    def stop(self):
        self.logger.debug('Stopping RFX thread (can take up to %ds)' % self.SELECT_TIMEOUT)
        self.terminated = True
        #self._Thread__stop()

    def handle_message(self, message):
        if message.get_schema_class() != 'sensor':
            return
        if message.get_schema_type() != 'basic':
            return

        msg_type = message.get_named_value_string('type')
        if msg_type == 'temp':
            # Check the device is an interesting one
            device = message.get_named_value_string('device')
            if self.config.is_sensor_known(device):
                value = message.get_named_value_float('current')
                units = message.get_named_value_string('units')
                name = self.config.get_sensor_name(device)

                # Insert data into database
                self.database.insert(device, name, value, units)
        elif msg_type == 'humidity':
            pass
        elif msg_type == 'power':
            pass
        elif msg_type == 'energy':
            pass
        elif msg_type == 'battery':
            pass
        else:
            self.logger.warning('Unknown sensor type "%s"' % msg_type)
