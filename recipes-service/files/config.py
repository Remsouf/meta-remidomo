#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Classes used to represent service config
"""
from calendar import TimeEncoding, day_name
import logging
import unittest
import xml.etree.ElementTree as ET
import datetime
from orders import Order, Schedule

DEFAULT_HYSTERESIS = 1.0
TAG_ROOT = 'remidomo'

TAG_SENSORS = 'sondes'
TAG_TEMPERATURE = 'temperature'
ATTRIB_ID = 'id'

TAG_HEATING = 'chauffage'

TAG_DAY = 'quotidien'
ATTRIB_NAME = 'jour'

TAG_HYSTERESIS = 'hysteresis'
ATTRIB_OVER = 'positif'
ATTRIB_UNDER = 'negatif'

TAG_ORDER = 'consigne'


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

        self.schedule = []
        for index in range(7):
            self.schedule.append(Schedule())

    def get_schedule(self, day):
        return self.schedule[day]

    def get_hysteresis_over(self):
        return self.hysteresis_over

    def get_hysteresis_under(self):
        return self.hysteresis_under

    def get_temperature_sensor_id(self):
        return self.temperature_sensor_id

    """
    Read a config (XML) file
    """
    def read_file(self, input_file):
        self.logger.info('Lecture du fichier de config : %s' % input_file)
        with open(input_file, 'r') as desc:
            self.parse_string(desc.read())

    """
    Parse a string containing the XML config
    """
    def parse_string(self, string):
        self.set_defaults()
        root = ET.fromstring(string)
        if root.tag != TAG_ROOT:
            raise ET.ParseError('Missing root tag %s' % TAG_ROOT)

        for child in root:
            if child.tag == TAG_HEATING:
                self.__parse_heating(child)
            elif child.tag == TAG_SENSORS:
                self.__parse_sensors(child)
            else:
                raise ET.ParseError('Unknown tag "%s"' % child.tag)

        return self

    def __parse_sensors(self, node):
        for child in node:
            if child.tag == TAG_TEMPERATURE:
                if ATTRIB_ID in child.attrib:
                    self.temperature_sensor_id = child.attrib[ATTRIB_ID]
                else:
                    raise ET.ParseError('Missing "%s" attribute for tag "%s"' % (ATTRIB_ID, TAG_TEMPERATURE))

    def __parse_heating(self, node):
        for child in node:
            if child.tag == TAG_HYSTERESIS:
                if ATTRIB_OVER in child.attrib:
                    self.hysteresis_over = float(child.attrib[ATTRIB_OVER])
                if ATTRIB_UNDER in child.attrib:
                    self.hysteresis_under = float(child.attrib[ATTRIB_UNDER])

            if child.tag == TAG_DAY:
                self.__parse_day(child)

    def __parse_day(self, node):
        # Convert day name to day index
        day = node.attrib[ATTRIB_NAME]
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
            self.schedule[day_index].append(order)
        except ET.ParseError, e:
            raise ET.ParseError('Day "%s" contains a bad order: %s' % (self.day_names[day_index], e.message))


class TestConfig(unittest.TestCase):
    DECIMAL_COMPARE_PLACES = 3

    def setUp(self):
        self.logger = logging.getLogger('Tests')

    def testNeedRoot(self):
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<pouet></pouet>')

    def testCannotParseBadHysteresis(self):
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage><hysteresis positif="a"></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage><hysteresis negatif="5b"></chauffage></remidomo>')

    def testCannotParseUnknownTag(self):
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><blah/></remidomo>')

    def testCanParseHysteresis(self):
        # Partially specified
        config = Config(self.logger).parse_string('<remidomo><chauffage><hysteresis positif="12.34"/></chauffage></remidomo>')
        self.assertAlmostEqual(12.34, config.get_hysteresis_over(), self.DECIMAL_COMPARE_PLACES)
        self.assertAlmostEqual(DEFAULT_HYSTERESIS, config.get_hysteresis_under(), self.DECIMAL_COMPARE_PLACES)

        # Also checks unspecified value gets assigned back to default !
        config.parse_string('<remidomo><chauffage><hysteresis negatif="34.21"/></chauffage></remidomo>')
        self.assertAlmostEqual(34.21, config.get_hysteresis_under(), self.DECIMAL_COMPARE_PLACES)
        self.assertAlmostEqual(DEFAULT_HYSTERESIS, config.get_hysteresis_over(), self.DECIMAL_COMPARE_PLACES)

        # Fully specified
        config.parse_string('<remidomo><chauffage><hysteresis positif="12.34" negatif="34.21"/></chauffage></remidomo>')
        self.assertAlmostEqual(12.34, config.get_hysteresis_over(), self.DECIMAL_COMPARE_PLACES)
        self.assertAlmostEqual(34.21, config.get_hysteresis_under(), self.DECIMAL_COMPARE_PLACES)

    def testCannotParseBadSensors(self):
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><sondes><temperature/></sondes></remidomo>')

    def testCanParseSensors(self):
        config = Config(self.logger).parse_string('<remidomo><sondes><temperature id="deadbeef"/></sondes></remidomo>')
        self.assertEqual('deadbeef', config.get_temperature_sensor_id())

    def testCannotParseBadDay(self):
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage><quotidien jour="blah"/></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage><quotidien jour="lundi"/><pouet/></chauffage></remidomo>')

    def testCanParseDays(self):
        config = Config(self.logger).parse_string('<remidomo><chauffage><quotidien jour="dimanche"><consigne debut="08:00" fin="16:00" temperature="12"/></quotidien></chauffage></remidomo>')
        self.assertEquals(1, config.get_schedule(6).get_orders_nb())
        self.assertEquals(0, config.get_schedule(0).get_orders_nb())

    def testCannotParseBadOrders(self):
        # Missing attributes
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage><quotidien jour="lundi"><consigne/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage><quotidien jour="lundi"><consigne fin="16:00" temperature="123"/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage><quotidien jour="lundi"><consigne debut="08:00" temperature="123"/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage><quotidien jour="lundi"><consigne debut="08:00" fin="16:00"/></quotidien></chauffage></remidomo>')

        # Bad times
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage><quotidien jour="lundi"><consigne debut="blah" fin="16:00" temperature="123"/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage><quotidien jour="lundi"><consigne debut="08:00" fin="blah" temperature="123"/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage><quotidien jour="lundi"><consigne debut="1.2" fin="16:00" temperature="123"/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage><quotidien jour="lundi"><consigne debut="08:00" fin="3.4" temperature="123"/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage><quotidien jour="lundi"><consigne debut="1234" fin="16:00" temperature="123"/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage><quotidien jour="lundi"><consigne debut="08:00" fin="4321" temperature="123"/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage><quotidien jour="lundi"><consigne debut="96:12" fin="16:00" temperature="123"/></quotidien></chauffage></remidomo>')
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage><quotidien jour="lundi"><consigne debut="08:00" fin="11:64" temperature="123"/></quotidien></chauffage></remidomo>')

        # Bad values
        with self.assertRaises(ET.ParseError):
            Config(self.logger).parse_string('<remidomo><chauffage><quotidien jour="lundi"><consigne debut="08:00" fin="16:00" temperature="abc"/></quotidien></chauffage></remidomo>')

    def testCanParseOrders(self):
        config = Config(self.logger).parse_string('<remidomo><chauffage><quotidien jour="dimanche"><consigne debut="08:00" fin="16:00" temperature="12"/><consigne debut="17:00" fin="18:00" temperature="21"/></quotidien></chauffage></remidomo>')
        self.assertAlmostEqual(12, config.get_schedule(6).get_order_for(datetime.time(9, 0)).get_value(), self.DECIMAL_COMPARE_PLACES)
        self.assertIsNone(config.get_schedule(6).get_order_for(datetime.time(7, 59)))
        self.assertAlmostEqual(21, config.get_schedule(6).get_order_for(datetime.time(17, 0)).get_value(), self.DECIMAL_COMPARE_PLACES)
        self.assertIsNone(config.get_schedule(6).get_order_for(datetime.time(19, 0)))


if __name__ == '__main__':
    unittest.main()
