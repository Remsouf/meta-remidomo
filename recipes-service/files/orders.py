#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Classes used to represent timed orders
"""
import unittest
from xml.etree.ElementTree import ParseError

ATTRIB_BEGIN = 'debut'
ATTRIB_END = 'fin'
ATTRIB_VALUE = 'temperature'

"""
A schedule, i.e. a set of orders for a same day
"""
class Schedule():
    def __init__(self):
        self.orders = []

    def add_order(self, order):
        self.orders.append(order)

    def get_order_for(self, time):
        for candidate in self.orders:
            if (candidate.begin <= time <= candidate.end):
                return candidate
        return None

    def get_orders_nb(self):
        return len(self.orders)

    def append(self, order):
        self.orders.append(order)


"""
An order, i.e. a time range and a value
"""
class Order():
    def __init__(self):
        self.begin = None
        self.end = None
        self.value = None

    def get_begin(self):
        return self.begin

    def get_end(self):
        return self.end

    def get_value(self):
        return self.value

    def parse(self, node):
        try:
            attr = node.attrib[ATTRIB_BEGIN]
        except KeyError:
            raise ParseError('Missing begin time')
        try:
            self.begin = int(attr)
        except ValueError:
            raise ParseError('Bad begin time "%s"' % attr)

        try:
            attr = node.attrib[ATTRIB_END]
        except KeyError:
            raise ParseError('Missing end time')
        try:
            self.end = int(attr)
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


if __name__ == '__main__':
    unittest.main()
