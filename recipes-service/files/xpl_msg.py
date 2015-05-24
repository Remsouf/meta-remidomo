#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest

"""
Exception raised when parsing fails
"""
class xPLException(Exception):
    pass


"""
Class to encapsulate an xPL message
"""
class xPLMessage:

    # schema types
    STATUS = 'xpl-stat'
    COMMAND = 'xpl-cmnd'
    TRIGGER = 'xpl-trig'

    # Mandatory header elements
    HOP = 'hop'
    SOURCE = 'source'
    TARGET = 'target'

    def __init__(self, message):
        self.named_values = {}
        self.__parse(message)

    def get_type(self):
        return self.msg_type

    def get_schema_type(self):
        return self.schema_type

    def get_schema_class(self):
        return self.schema_class

    def has_named_value(self, name):
        return name in self.named_values

    def get_named_value_string(self, name):
        try:
            return self.named_values[name]
        except KeyError:
            return None

    def get_named_value_float(self, name):
        try:
            return float(self.named_values[name])
        except KeyError:
            return None

    def get_named_value_int(self, name):
        try:
            return int(self.named_values[name])
        except KeyError:
            return None

    def get_hop_count(self):
        return self.hop_count

    def get_source(self):
        return self.source

    def get_target(self):
        return self.target

    """
    Parse any name=value pair
    """
    @staticmethod
    def __parse_named_value(line):
        tokens = line.split('=')
        if len(tokens) != 2:
            raise xPLException('Malformed name-value pair "%s"' % line)
        return tokens[0], tokens[1]

    """
    Parse message type:
    xpl-cmnd
    """
    def __parse_type(self, lines):
        if len(lines) == 0:
            raise xPLException('Missing message type')
        msg_type = lines[0].strip()
        if (msg_type != self.COMMAND and
            msg_type != self.STATUS and
            msg_type != self.TRIGGER):
            raise xPLException('Unknown message type "%s"' % type)

        self.msg_type = msg_type
        lines.pop(0)
        return lines

    """
    Parse header:
    {
        hop=1
        source=xpl-xplhal.myhouse
        target=acme-cm12.server
    }
    """
    def __parse_header(self, lines):
        if len(lines) == 0:
            raise xPLException('Missing message header')
        if lines[0] != '{':
            raise xPLException('Expected header start, instead got "%s"' % lines[0])
        lines.pop(0)

        hop_given = False
        source_given = False
        target_given = False

        while True:
            data = lines[0].strip()

            # End of header ?
            if data == '}':
                lines.pop(0)
                break

            # Get name/value pair
            name, value = self.__parse_named_value(data)
            if name == self.HOP:
                try:
                    self.hop_count = int(value)
                except ValueError:
                    raise xPLException('Unexpected hop count "%s"' % value)
                hop_given = True
            elif name == self.SOURCE:
                self.source = value
                source_given = True
            elif name == self.TARGET:
                self.target = value
                target_given = True
            else:
                raise xPLException('Unknown header data "%s"' % name)
            lines.pop(0)

            if len(lines) == 0:
                raise xPLException('Header not closed')

        if not hop_given:
            raise xPLException('Missing hop count in header')
        if not source_given:
            raise xPLException('Missing source in header')
        if not target_given:
            raise xPLException('Missing target in header')

        return lines

    """
    Parse schema:
    x10.basic
    """
    def __parse_schema(self, lines):
        if len(lines) == 0:
            raise xPLException('Missing message schema')
        schema = lines[0].strip()
        tokens = schema.split('.')
        if len(tokens) != 2:
            raise xPLException('Malformed schema "%s"' % schema)
        self.schema_class = tokens[0]
        self.schema_type = tokens[1]
        lines.pop(0)
        return lines

    """
    Parse body:
    {
        command=dim
        device=a1
        level=75
    }
    """
    def __parse_body(self, lines):
        if len(lines) == 0:
            raise xPLException('Missing message body')
        if lines[0] != '{':
            raise xPLException('Expected body start, instead got "%s"' % lines[0])
        lines.pop(0)

        while True:
            data = lines[0].strip()

            # End of body ?
            if data == '}':
                lines.pop(0)
                break

            name, value = self.__parse_named_value(data)
            self.named_values[name] = value
            lines.pop(0)

            if len(lines) == 0 or len(lines[0]) == 0:
                raise xPLException('Body not closed')

        return lines

    def __parse(self, message):
        if message is None or len(message) == 0:
            raise xPLException('Message is empty')

        lines = message.split('\n')
        lines = self.__parse_type(lines)
        lines = self.__parse_header(lines)
        lines = self.__parse_schema(lines)
        lines = self.__parse_body(lines)

        if len(lines) > 0:
            raise xPLException('Unexpected garbage after message body, starting with "%s"' % lines[0])


class TestXPL(unittest.TestCase):
    DECIMAL_COMPARE_PLACES = 3

    def testCannotParseNothing(self):
        with self.assertRaises(xPLException):
            xPLMessage('')

    def testCannotParseGarbage(self):
        with self.assertRaises(xPLException):
            xPLMessage('blah blah')

    def testCannotParseBadCommand(self):
        with self.assertRaises(xPLException):
            xPLMessage('xpl-cmn\n{\nhop=1\nsource=myhouse\ntarget=server\n}')

    def testCannotParseBadHeader(self):
        with self.assertRaises(xPLException):
            xPLMessage('xpl-cmnd\nhi!\nhop=1\nsource=myhouse\ntarget=server\n}')
        with self.assertRaises(xPLException):
            xPLMessage('xpl-cmnd\n{\nhop1\nsource=myhouse\ntarget=server\n}')
        with self.assertRaises(xPLException):
            xPLMessage('xpl-cmnd\n{\nhop=blah\nsource=myhouse\ntarget=server\n}')
        with self.assertRaises(xPLException):
            xPLMessage('xpl-cmnd\n{\nsource=myhouse\ntarget=server\n}')
        with self.assertRaises(xPLException):
            xPLMessage('xpl-cmnd\n{\nhop=1\ntarget=server\n}')
        with self.assertRaises(xPLException):
            xPLMessage('xpl-cmnd\n{\nhop=1\nsource=myhouse\n}')
        with self.assertRaises(xPLException):
            xPLMessage('xpl-cmnd\n{\nhop1\nsource=myhouse\ntarget=server\ndummy=plop\n}')
        with self.assertRaises(xPLException):
            xPLMessage('xpl-cmnd\n{\nhop1\nsource=myhouse\ntarget=server\n')

    def testCannotParseBadSchema(self):
        with self.assertRaises(xPLException):
            xPLMessage('xpl-cmnd\n{\nhop=1\nsource=myhouse\ntarget=server\n}\nx10basic')
        with self.assertRaises(xPLException):
            xPLMessage('xpl-cmnd\n{\nhop=1\nsource=myhouse\ntarget=server\n}\nx10.')
        with self.assertRaises(xPLException):
            xPLMessage('xpl-cmnd\n{\nhop=1\nsource=myhouse\ntarget=server\n}\n.basic')

    def testCannotParseBadBody(self):
        with self.assertRaises(xPLException):
            xPLMessage('xpl-cmnd\n{\nhop=1\nsource=myhouse\ntarget=server\n}\nx10.basic\n')
        with self.assertRaises(xPLException):
            xPLMessage('xpl-cmnd\n{\nhop=1\nsource=myhouse\ntarget=server\n}\nx10.basic\n{\n')
        with self.assertRaises(xPLException):
            xPLMessage('xpl-cmnd\n{\nhop=1\nsource=myhouse\ntarget=server\n}\nx10.basic\n{\nbip=\n')
        with self.assertRaises(xPLException):
            xPLMessage('xpl-cmnd\n{\nhop=1\nsource=myhouse\ntarget=server\n}\nx10.basic\n{\nbip=bop\n')
        with self.assertRaises(xPLException):
            xPLMessage('xpl-cmnd\n{\nhop=1\nsource=myhouse\ntarget=server\n}\nx10.basic\n{\nbip=bop\n}\n')

    def testCannotParseGarbageAfterBody(self):
        with self.assertRaises(xPLException):
            xPLMessage('xpl-cmnd\n{\nhop=1\nsource=myhouse\ntarget=server\n}\nx10.basic\n{\nbip=bop\n}\nblah!\n')

    def testCanParseNominal(self):
        msg = xPLMessage('xpl-cmnd\n{\nhop=1\nsource=myhouse\ntarget=server\n}\nx10.basic\n{\nbip=bop\nint=12\nfloat=12.5\n}')
        self.assertEqual(xPLMessage.COMMAND, msg.get_type())
        self.assertEqual(1, msg.get_hop_count())
        self.assertEqual('myhouse', msg.get_source())
        self.assertEqual('server', msg.get_target())
        self.assertEqual('x10', msg.get_schema_class())
        self.assertEqual('basic', msg.get_schema_type())
        self.assertEqual('bop', msg.get_named_value_string('bip'))
        self.assertEqual(12, msg.get_named_value_int('int'))
        self.assertAlmostEqual(12.5, msg.get_named_value_float('float'), self.DECIMAL_COMPARE_PLACES)
        with self.assertRaises(ValueError):
            msg.get_named_value_int('bip')
        self.assertIsNone(msg.get_named_value_string('prout'))


if __name__ == '__main__':
    unittest.main()
