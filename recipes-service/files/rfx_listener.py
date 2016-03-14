#!/usr/bin/python
# -*- coding: utf-8 -*-

from threading import Thread, RLock
import select
import socket
from database import Database, TYPE_TEMP, TYPE_POWER, TYPE_HUMIDITY
from xpl_msg import xPLMessage

lock = RLock()


class RFXListener(Thread):
    """
    Class to implement a thread listening to rfx-lan messages
    """

    # RFX packets are rather small...
    RECV_SIZE = 512

    # Broadcast address
    BROADCAST_IP = '255.255.255.255'

    # Select timeout
    SELECT_TIMEOUT = 10

    def __init__(self, config, database, executor, logger):
        Thread.__init__(self)
        self.config = config
        self.executor = executor
        self.logger = logger
        self.database = database
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
            if len(readable) > 0:
                data, _ = sock.recvfrom(self.RECV_SIZE)
                msg = xPLMessage(data)
                self.handle_message(msg)

    def stop(self):
        self.logger.debug('Stopping RFX thread (can take up to %ds)' % self.SELECT_TIMEOUT)
        self.terminated = True
        # self._Thread__stop()

    def handle_message(self, message):
        if message.get_schema_class() != 'sensor':
            return
        if message.get_schema_type() != 'basic':
            return

        self.executor.blink_sensor()

        msg_type = message.get_named_value_string('type')
        if msg_type == 'temp':
            # Check the device is an interesting one
            device = message.get_named_value_string('device')
            if self.config.is_sensor_known(device):
                value = message.get_named_value_float('current')
                units = message.get_named_value_string('units')
                name = self.config.get_temp_sensor_name(device)

                # Insert data into database
                self.database.insert(device, name, value, units, TYPE_TEMP)
            else:
                self.logger.debug('Ignored temperature device %s' % device)
        elif msg_type == 'humidity':
            # Check the device is an interesting one
            device = message.get_named_value_string('device')
            if self.config.is_sensor_known(device):
                value = message.get_named_value_float('current')
                units = message.get_named_value_string('units')
                name = self.config.get_temp_sensor_name(device)

                # Insert data into database
                self.database.insert(device, name, value, units, TYPE_HUMIDITY)
        elif msg_type == 'power':
            # Check the device is an interesting one
            device = message.get_named_value_string('device')
            if self.config.is_sensor_known(device):
                value = message.get_named_value_float('current')
                units = message.get_named_value_string('units')
                name = self.config.get_power_sensor_name(device)

                # Insert data into database
                self.database.insert(device, name, value, units, TYPE_POWER)
        elif msg_type == 'energy':
            pass
        elif msg_type == 'battery':
            pass
        else:
            self.logger.warning('Unknown sensor type "%s"' % msg_type)
