#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Classes used to represent timed orders
"""
import unittest
from xml.etree.ElementTree import ParseError
import datetime
import dateutil

ATTRIB_BEGIN = 'debut'
ATTRIB_END = 'fin'
ATTRIB_VALUE = 'temperature'

FULL_DATETIME_FORMAT = '%d/%m/%Y %H:%M'


def time_to_js(time):
    return 'new Date(0,0,0,%d,%d)' % (time.hour, time.minute)


"""
A schedule, i.e. a set of orders for a same day
"""
class Schedule:
    def __init__(self):
        self.orders = []

    def add_order(self, order):
        self.orders.append(order)

    def get_order_for(self, time):
        for candidate in self.orders:
            if candidate.begin <= time <= candidate.end:
                return candidate
        return None

    def get_orders_nb(self):
        return len(self.orders)

    def is_empty(self):
        return self.get_orders_nb() == 0

    def get_orders(self):
        return self.orders


"""
An order, i.e. a time range and a value
"""
class Order:
    def __init__(self, begin=None, end=None, value=None):
        self.begin = begin
        self.end = end
        self.value = value

    def get_begin(self):
        return self.begin

    def get_begin_js(self):
        return time_to_js(self.begin)

    def get_end(self):
        return self.end

    def get_end_js(self):
        return time_to_js(self.end)

    def get_value(self):
        return self.value

    def parse(self, node):
        try:
            attr = node.attrib[ATTRIB_BEGIN]
        except KeyError:
            raise ParseError('Missing begin time')

        numbers = attr.split(':')
        if len(numbers) != 2:
            raise ParseError('Bad begin time "%s"' % attr)
        try:
            self.begin = datetime.time(int(numbers[0]), int(numbers[1]), 0)
        except ValueError:
            raise ParseError('Bad begin time "%s"' % attr)

        try:
            attr = node.attrib[ATTRIB_END]
        except KeyError:
            raise ParseError('Missing end time')

        numbers = attr.split(':')
        if len(numbers) != 2:
            raise ParseError('Bad end time "%s"' % attr)
        try:
            self.end = datetime.time(int(numbers[0]), int(numbers[1]), 0)
        except ValueError:
            raise ParseError('Bad end time "%s"' % attr)

        try:
            attr = node.attrib[ATTRIB_VALUE]
        except KeyError:
            raise ParseError('Missing value')
        try:
            self.value = float(attr)
        except ValueError:
            raise ParseError('Bad order value "%s"' % attr)

    def generateXml(self, node):
        node.set(ATTRIB_BEGIN, self.get_begin().strftime('%H:%M'))

        # If end_time is the end of day (00:00 the day after), decrease one minute
        end_time = self.get_end()
        if end_time.hour == 0 and end_time.minute == 0:
            end_time.replace(hour=23, minute=59)
        node.set(ATTRIB_END, end_time.strftime('%H:%M'))
        node.set(ATTRIB_VALUE, str(self.get_value()))


"""
An override, with a fixed value during a limited amount of time
(similar to an order, but with date+time instead of just time)
"""
class Override:
    def __init__(self, begin=None, end=None, value=None):
        self.begin = begin
        self.end = end
        self.value = value

    def get_begin(self):
        return self.begin

    def get_end(self):
        return self.end

    def get_value(self):
        return self.value

    def is_valid(self):
        return self.end > self.begin

    def parse(self, node):
        try:
            attr = node.attrib[ATTRIB_BEGIN]
        except KeyError:
            raise ParseError('Missing begin time')

        try:
            self.begin = datetime.datetime.strptime(attr, FULL_DATETIME_FORMAT)
        except ValueError:
            raise ParseError('Bad begin time "%s"' % attr)

        try:
            attr = node.attrib[ATTRIB_END]
        except KeyError:
            raise ParseError('Missing end time')

        try:
            self.end = datetime.datetime.strptime(attr, FULL_DATETIME_FORMAT)
        except ValueError:
            raise ParseError('Bad end time "%s"' % attr)

        try:
            attr = node.attrib[ATTRIB_VALUE]
        except KeyError:
            raise ParseError('Missing value')
        try:
            self.value = float(attr)
        except ValueError:
            raise ParseError('Bad override value "%s"' % attr)

    def generateXml(self, node):
        node.set(ATTRIB_BEGIN, self.begin.strftime(FULL_DATETIME_FORMAT))
        node.set(ATTRIB_END, self.end.strftime(FULL_DATETIME_FORMAT))
        node.set(ATTRIB_VALUE, str(self.get_value()))


if __name__ == '__main__':
    unittest.main()
