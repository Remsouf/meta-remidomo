#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Classes used to represent service config
"""
from calendar import TimeEncoding, day_name
import logging
import unittest
from xml.dom import minidom
import xml.etree.ElementTree as ET
import datetime
from orders import Order, Schedule, Override

DEFAULT_HYSTERESIS = 1.0
DEFAULT_RFXLAN_PORT = 3865

TAG_ROOT = 'remidomo'

TAG_SENSORS = 'rfxlan'
TAG_TEMPERATURE = 'temperature'
TAG_POWER = 'puissance'
ATTRIB_ID = 'id'
ATTRIB_NAME = 'nom'
ATTRIB_PORT = 'port'

TAG_HEATING = 'chauffage'
ATTRIB_SENSOR = 'capteur'
ATTRIB_SWITCH = 'mode'
VALUE_ON = 'on'
VALUE_OFF = 'off'

TAG_DAY = 'quotidien'
ATTRIB_DAY_NAME = 'jour'

TAG_HYSTERESIS = 'hysteresis'
ATTRIB_OVER = 'positif'
ATTRIB_UNDER = 'negatif'

TAG_ORDER = 'consigne'

TAG_OVERRIDE = 'derogation'


class Config:

    def __init__(self, logger):
        self.logger = logger

        # Build the list of day names
        self.day_names = []
        with TimeEncoding("fr_FR") as encoding:
            for index in range(7):
                s = day_name[index]
                if encoding is not None:
                    self.day_names.append(s.decode(encoding))

        self.set_defaults()

    def set_defaults(self):
        self.hysteresis_over = DEFAULT_HYSTERESIS
        self.hysteresis_under = DEFAULT_HYSTERESIS
        self.temperature_sensor_id = None
        self.rfxlan_port = DEFAULT_RFXLAN_PORT
        self.heating_enabled = False
        self.clear_schedules()
        self.temp_sensors = {}
        self.power_sensors = {}
        self.heating_sensor_name = ''
        self.override = None

    def get_day_names(self):
        return self.day_names

    def get_order_for(self, datetime):
        # Is there an override ?
        override = self.get_override_for(datetime)
        if override:
            return override

        schedule = self.get_schedule(datetime.weekday())
        return schedule.get_order_for(datetime.get_time())

    def get_schedule(self, day):
        return self.schedule[day]

    def clear_schedules(self):
        self.schedule = []
        for index in range(7):
            self.schedule.append(Schedule())

    def add_order(self, day, order):
        self.schedule[day].add_order(order)

    def get_hysteresis_over(self):
        return self.hysteresis_over

    def get_hysteresis_under(self):
        return self.hysteresis_under

    def get_temp_sensor_name(self, id):
        for (name, candidate) in self.temp_sensors.items():
            if candidate == id:
                return name
        else:
            return None

    def get_power_sensor_name(self, id):
        for (name, candidate) in self.power_sensors.items():
            if candidate == id:
                return name
        else:
            return None

    def is_sensor_known(self, id):
        is_temperature = self.get_temp_sensor_name(id) is not None
        is_power = self.get_power_sensor_name(id) is not None
        return is_temperature or is_power

    def is_heating_enabled(self):
        return self.heating_enabled

    def get_temp_sensor_id(self, name):
        if name in self.temp_sensors:
            return self.temp_sensors[name]
        else:
            return None

    def get_temp_sensor_names(self):
        return self.temp_sensors.keys()

    def get_temp_sensors(self):
        return self.temp_sensors

    def get_heating_sensor_name(self):
        return self.heating_sensor_name

    def get_power_sensors(self):
        return self.power_sensors

    def get_rfxlan_port(self):
        return self.rfxlan_port

    def set_hysteresis_over(self, value):
        self.hysteresis_over = value

    def set_hysteresis_under(self, value):
        self.hysteresis_under = value

    def set_rfxlan_port(self, port):
        self.rfxlan_port = port

    def clear_temp_sensors(self):
        self.temp_sensors.clear()

    def clear_power_sensors(self):
        self.power_sensors.clear()

    def add_temp_sensor(self, name, address):
        self.temp_sensors[name] = address

    def set_heating_sensor_name(self, name):
        self.heating_sensor_name = name

    def set_heating_enabled(self, flag):
        self.heating_enabled = flag

    def add_power_sensor(self, name, address):
        self.power_sensors[name] = address

    def set_override(self, override):
        if override.is_valid():
            self.override = override
        else:
            self.override = None

    def get_override(self):
        return self.override

    def get_override_for(self, datetime):
        if self.override is None:
            return None
        if self.override.begin <= datetime <= self.override.end:
            return self.override

    def clear_override(self):
        self.override = None

    def save(self, output_file):
        """
        Write a config (XML) file
        """
        self.logger.info('Ecriture du fichier de config : %s' % output_file)
        with open(output_file, 'w') as desc:
            desc.write(self.to_xml())

    def read_file(self, input_file):
        """
        Read a config (XML) file
        """
        self.logger.info('Lecture du fichier de config : %s' % input_file)
        with open(input_file, 'r') as desc:
            try:
                self.parse_string(desc.read())
            except ET.ParseError, e:
                self.logger.error('Erreur de parsing : %s' % e.message)

    def parse_string(self, string):
        """
        Parse a string containing the XML config
        """
        self.set_defaults()
        root = ET.fromstring(string)
        if root.tag != TAG_ROOT:
            raise ET.ParseError('Missing root tag %s' % TAG_ROOT)

        for child in root:
            if child.tag == TAG_HEATING:
                self.__parse_heating(child)
            elif child.tag == TAG_SENSORS:
                self.__parse_rfxlan(child)
            else:
                raise ET.ParseError('Unknown tag "%s"' % child.tag)

        return self

    def __parse_rfxlan(self, node):
        if ATTRIB_PORT not in node.attrib:
            raise ET.ParseError('Missing "%s" attribute in "%s" tag' % (ATTRIB_PORT, TAG_SENSORS))
        try:
            self.rfxlan_port = int(node.attrib[ATTRIB_PORT])
        except ValueError:
            raise ET.ParseError('Bad rfxlan port "%s"' % node.attrib[ATTRIB_PORT])
        for child in node:
            if child.tag == TAG_TEMPERATURE:
                if ATTRIB_ID in child.attrib:
                    id = child.attrib[ATTRIB_ID]
                else:
                    raise ET.ParseError('Missing "%s" attribute for tag "%s"' % (ATTRIB_ID, TAG_TEMPERATURE))
                if ATTRIB_NAME in child.attrib:
                    name = child.attrib[ATTRIB_NAME]
                else:
                    raise ET.ParseError('Missing "%s" attribute for tag "%s"' % (ATTRIB_NAME, TAG_TEMPERATURE))
                self.temp_sensors[name] = id
            elif child.tag == TAG_POWER:
                if ATTRIB_ID in child.attrib:
                    id = child.attrib[ATTRIB_ID]
                else:
                    raise ET.ParseError('Missing "%s" attribute for tag "%s"' % (ATTRIB_ID, TAG_POWER))
                if ATTRIB_NAME in child.attrib:
                    name = child.attrib[ATTRIB_NAME]
                else:
                    raise ET.ParseError('Missing "%s" attribute for tag "%s"' % (ATTRIB_NAME, TAG_POWER))
                self.power_sensors[name] = id

    def __parse_heating(self, node):
        if ATTRIB_SENSOR in node.attrib:
            self.heating_sensor_name = node.attrib[ATTRIB_SENSOR]
        else:
            raise ET.ParseError('Missing "%s" attribute for tag "%s"' % (ATTRIB_SENSOR, TAG_HEATING))

        if ATTRIB_SWITCH in node.attrib:
            if node.attrib[ATTRIB_SWITCH] == VALUE_ON:
                self.heating_enabled = True
            elif node.attrib[ATTRIB_SWITCH] == VALUE_OFF:
                self.heating_enabled = False
            else:
                raise ET.ParseError('Wrong value "%s" for attribute "%s"' % (node.attrib[ATTRIB_SWITCH], ATTRIB_SWITCH))
        else:
            raise ET.ParseError('Missing "%s" attribute for tag "%s"' % (ATTRIB_SWITCH, TAG_HEATING))

        for child in node:
            if child.tag == TAG_HYSTERESIS:
                if ATTRIB_OVER in child.attrib:
                    self.hysteresis_over = float(child.attrib[ATTRIB_OVER])
                if ATTRIB_UNDER in child.attrib:
                    self.hysteresis_under = float(child.attrib[ATTRIB_UNDER])

            if child.tag == TAG_DAY:
                self.__parse_day(child)

            if child.tag == TAG_OVERRIDE:
                self.__parse_override(child)

    def __parse_day(self, node):
        # Convert day name to day index
        if ATTRIB_DAY_NAME in node.attrib:
            day = node.attrib[ATTRIB_DAY_NAME]
        else:
            raise ET.ParseError('Missing "%s" attribute for tag "%s"' % (ATTRIB_DAY_NAME, TAG_DAY))
        day_index = 0
        for day_candidate in self.day_names:
            if day == day_candidate:
                break
            day_index += 1
        else:
            raise ET.ParseError('Day "%s" is not a valid day name' % day)

        has_orders = False
        for child in node:
            if child.tag == TAG_ORDER:
                has_orders = True
                self.__parse_order(child, day_index)
            else:
                raise ET.ParseError('Day "%s" contains an unknown tag "%s"' % (day, child.tag))

        if not has_orders:
            raise ET.ParseError('Day "%s" contains no orders' % day)

    def __parse_order(self, node, day_index):
        try:
            order = Order()
            order.parse(node)
            self.schedule[day_index].add_order(order)
        except ET.ParseError, e:
            raise ET.ParseError('Day "%s" contains a bad order: %s' % (self.day_names[day_index], e.message))

    def __parse_override(self, node):
        try:
            override = Override()
            override.parse(node)
            self.override = override
        except ET.ParseError, e:
            raise ET.ParseError('Bad override: %s' % e.message)

    def to_xml(self):
        """
        Build XML string describing config
        """
        root = ET.Element(TAG_ROOT)
        rfxlan = ET.SubElement(root, TAG_SENSORS)
        rfxlan.set(ATTRIB_PORT, str(self.get_rfxlan_port()))

        for name, id in self.temp_sensors.items():
            temp = ET.SubElement(rfxlan, TAG_TEMPERATURE)
            temp.set(ATTRIB_ID, id)
            temp.set(ATTRIB_NAME, name)

        for name, id in self.power_sensors.items():
            power = ET.SubElement(rfxlan, TAG_POWER)
            power.set(ATTRIB_ID, id)
            power.set(ATTRIB_NAME, name)

        chauffage = ET.SubElement(root, TAG_HEATING)
        chauffage.set(ATTRIB_SENSOR, self.get_heating_sensor_name())
        chauffage.set(ATTRIB_SWITCH, VALUE_ON if self.is_heating_enabled() else VALUE_OFF)

        hysteresis = ET.SubElement(chauffage, TAG_HYSTERESIS)
        hysteresis.set(ATTRIB_OVER, str(self.get_hysteresis_over()))
        hysteresis.set(ATTRIB_UNDER, str(self.get_hysteresis_under()))

        for index, day_name in enumerate(self.get_day_names()):
            day = ET.SubElement(chauffage, TAG_DAY)
            day.set(ATTRIB_DAY_NAME, day_name)

            for order in self.get_schedule(index).get_orders():
                order_node = ET.SubElement(day, TAG_ORDER)
                order.generateXml(order_node)

        if self.override:
            override_node = ET.SubElement(chauffage, TAG_OVERRIDE)
            self.override.generateXml(override_node)

        string = ET.tostring(root)
        reparsed = minidom.parseString(string)
        return reparsed.toprettyxml(indent="  ")


class TestConfig(unittest.TestCase):
    DECIMAL_COMPARE_PLACES = 3

    def setUp(self):
        self.logger = logging.getLogger('Tests')

    def testNeedRoot(self):
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<pouet></pouet>')

    def testCannotParseIncompleteHeatingTag(self):
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur=""></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage mode="on"></chauffage></remidomo>')

    def testCannotParseBadHeatingMode(self):
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode=""></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="blah"></chauffage></remidomo>')

    def testCannotParseBadHysteresis(self):
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><hysteresis positif="a"></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><hysteresis negatif="5b"></chauffage></remidomo>')

    def testCannotParseUnknownTag(self):
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><blah/></remidomo>')

    def testCanParseHeating(self):
        config = Config(self.logger).parse_string('<remidomo><chauffage capteur="essai" mode="on"></chauffage></remidomo>')
        self.assertEqual("essai", config.get_heating_sensor_name())
        self.assertEqual(True, config.is_heating_enabled())

        config = Config(self.logger).parse_string('<remidomo><chauffage capteur="essai" mode="off"></chauffage></remidomo>')
        self.assertEqual(False, config.is_heating_enabled())

    def testCanParseHysteresis(self):
        # Partially specified
        config = Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><hysteresis positif="12.34"/></chauffage></remidomo>')
        self.assertAlmostEqual(12.34, config.get_hysteresis_over(), self.DECIMAL_COMPARE_PLACES)
        self.assertAlmostEqual(DEFAULT_HYSTERESIS, config.get_hysteresis_under(), self.DECIMAL_COMPARE_PLACES)

        # Also checks unspecified value gets assigned back to default !
        config.parse_string('<remidomo><chauffage capteur="" mode="on"><hysteresis negatif="34.21"/></chauffage></remidomo>')
        self.assertAlmostEqual(34.21, config.get_hysteresis_under(), self.DECIMAL_COMPARE_PLACES)
        self.assertAlmostEqual(DEFAULT_HYSTERESIS, config.get_hysteresis_over(), self.DECIMAL_COMPARE_PLACES)

        # Fully specified
        config.parse_string('<remidomo><chauffage capteur="" mode="on"><hysteresis positif="12.34" negatif="34.21"/></chauffage></remidomo>')
        self.assertAlmostEqual(12.34, config.get_hysteresis_over(), self.DECIMAL_COMPARE_PLACES)
        self.assertAlmostEqual(34.21, config.get_hysteresis_under(), self.DECIMAL_COMPARE_PLACES)

    def testCannotParseBadSensors(self):
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><rfxlan port="1234"><temperature/></rfxlan></remidomo>')

    def testCanParseSensors(self):
        config = Config(self.logger).parse_string('<remidomo><rfxlan port="1234"><temperature id="deadbeef" nom="bidule"/></rfxlan><chauffage capteur="bidule" mode="on"/></remidomo>')
        self.assertEqual('deadbeef', config.get_temp_sensor_id('bidule'))
        self.assertEqual('bidule', config.get_temp_sensor_name('deadbeef'))
        self.assertEqual('bidule', config.get_heating_sensor_name())
        self.assertEqual(1234, config.get_rfxlan_port())

    def testCannotParseBadRfxPort(self):
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><rfxlan></rfxlan></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><rfxlan port="blah"></rfxlan></remidomo>')

    def testCannotParseBadDay(self):
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><quotidien jour="blah"/></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><quotidien jour="lundi"/><pouet/></chauffage></remidomo>')

    def testCanParseDays(self):
        config = Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><quotidien jour="dimanche"><consigne debut="08:00" fin="16:00" temperature="12"/></quotidien></chauffage></remidomo>')
        self.assertEquals(1, config.get_schedule(6).get_orders_nb())
        self.assertEquals(0, config.get_schedule(0).get_orders_nb())

    def testCannotParseBadOrders(self):
        # Missing attributes
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><quotidien jour="lundi"><consigne/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><quotidien jour="lundi"><consigne fin="16:00" temperature="123"/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><quotidien jour="lundi"><consigne debut="08:00" temperature="123"/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><quotidien jour="lundi"><consigne debut="08:00" fin="16:00"/></quotidien></chauffage></remidomo>')

        # Bad times
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><quotidien jour="lundi"><consigne debut="blah" fin="16:00" temperature="123"/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><quotidien jour="lundi"><consigne debut="08:00" fin="blah" temperature="123"/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><quotidien jour="lundi"><consigne debut="1.2" fin="16:00" temperature="123"/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><quotidien jour="lundi"><consigne debut="08:00" fin="3.4" temperature="123"/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><quotidien jour="lundi"><consigne debut="1234" fin="16:00" temperature="123"/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><quotidien jour="lundi"><consigne debut="08:00" fin="4321" temperature="123"/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><quotidien jour="lundi"><consigne debut="96:12" fin="16:00" temperature="123"/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><quotidien jour="lundi"><consigne debut="08:00" fin="11:64" temperature="123"/></quotidien></chauffage></remidomo>')

        # Bad values
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><quotidien jour="lundi"><consigne debut="08:00" fin="16:00" temperature="abc"/></quotidien></chauffage></remidomo>')

    def testCanParseOrders(self):
        config = Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><quotidien jour="dimanche"><consigne debut="08:00" fin="16:00" temperature="12"/><consigne debut="17:00" fin="18:00" temperature="21"/></quotidien></chauffage></remidomo>')
        self.assertAlmostEqual(12, config.get_schedule(6).get_order_for(datetime.time(9, 0)).get_value(), self.DECIMAL_COMPARE_PLACES)
        self.assertIsNone(config.get_schedule(6).get_order_for(datetime.time(7, 59)))
        self.assertAlmostEqual(21, config.get_schedule(6).get_order_for(datetime.time(17, 0)).get_value(), self.DECIMAL_COMPARE_PLACES)
        self.assertIsNone(config.get_schedule(6).get_order_for(datetime.time(19, 0)))

    def testCanSaveFile(self):
        config = Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="on"><quotidien jour="dimanche"><consigne debut="08:00" fin="16:00" temperature="12"/><consigne debut="17:00" fin="18:15" temperature="21"/></quotidien></chauffage></remidomo>')
        self.assertEqual('<?xml version="1.0" ?>\n<remidomo>\n  <rfxlan port="3865"/>\n  <chauffage capteur="" mode="on">\n    <hysteresis negatif="1.0" positif="1.0"/>\n    ' +
                         '<quotidien jour="lundi"/>\n    <quotidien jour="mardi"/>\n    <quotidien jour="mercredi"/>\n    <quotidien jour="jeudi"/>\n    <quotidien jour="vendredi"/>\n    ' +
                         '<quotidien jour="samedi"/>\n    <quotidien jour="dimanche">\n      <consigne debut="08:00" fin="16:00" temperature="12.0"/>\n      <consigne debut="17:00" fin="18:15" temperature="21.0"/>\n    ' +
                         '</quotidien>\n  </chauffage>\n</remidomo>\n', config.to_xml())

        config = Config(self.logger).parse_string('<remidomo><chauffage capteur="" mode="off"><hysteresis positif="12.34" negatif="34.21"/></chauffage></remidomo>')
        self.assertEqual('<?xml version="1.0" ?>\n<remidomo>\n  <rfxlan port="3865"/>\n  <chauffage capteur="" mode="off">\n    <hysteresis negatif="34.21" positif="12.34"/>\n    ' +
                         '<quotidien jour="lundi"/>\n    <quotidien jour="mardi"/>\n    <quotidien jour="mercredi"/>\n    <quotidien jour="jeudi"/>\n    ' +
                         '<quotidien jour="vendredi"/>\n    <quotidien jour="samedi"/>\n    <quotidien jour="dimanche"/>\n  </chauffage>\n</remidomo>\n', config.to_xml())

    def testCanParseOverride(self):
        config = Config(self.logger).parse_string('<remidomo><chauffage capteur="essai" mode="on"></chauffage></remidomo>')
        self.assertIsNone(config.get_override())

        config = Config(self.logger).parse_string('<remidomo><chauffage capteur="essai" mode="on"><derogation debut="21/10/2015 14:00" fin="21/10/2015 14:05" temperature="123"/></chauffage></remidomo>')
        self.assertAlmostEqual(123, config.get_override_for(datetime.datetime(2015, 10, 21, 14, 2)).get_value(), self.DECIMAL_COMPARE_PLACES)
        self.assertIsNone(config.get_override_for(datetime.datetime(2015, 10, 21, 13, 59)))
        self.assertIsNone(config.get_override_for(datetime.datetime(2015, 10, 21, 14, 06)))
        self.assertIsNone(config.get_override_for(datetime.datetime(2015, 10, 22, 14, 2)))

    def testCannotParseBadOverride(self):
        # Missing attributes
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="essai" mode="on"><derogation/></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="essai" mode="on"><derogation fin="14/01/1977 12:00" temperature="123"/></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="essai" mode="on"><derogation debut="14/01/1977 12:00" temperature="123"/></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="essai" mode="on"><derogation debut="14/01/1977 08:00" fin="14/01/1977 12:00"/></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="essai" mode="on"><derogation debut="14/01/1977 08:00" fin="14/01/1977 12:00" temperature="abc"/></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage capteur="essai" mode="on"><derogation debut="14/01|1977 08:00" fin="14/01/1977 12:00" temperature="123"/></chauffage></remidomo>')


if __name__ == '__main__':
    unittest.main()
