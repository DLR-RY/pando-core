#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, German Aerospace Center (DLR)
#
# This file is part of the development version of the pando library.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Authors:
# - 2017, Fabian Greif (DLR RY-AVS)

import os
import unittest

import pando

class ParameterByteOrderTest(unittest.TestCase):

    def setUp(self):
        self.model = self.parse_file("resources/parameter_byte_order.xml")

    def parse_file(self, filename):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", filename)
        parser = pando.parser.Parser()
        model = parser.parse(filepath)

        self.assertIsNotNone(model)
        return model

    def test_parameters_should_be_big_endian_by_default(self):
        parameter = self.model.parameters["parameter_default"]
        self.assertEqual(pando.model.ByteOrder.BIG_ENDIAN, parameter.byte_order)

    def test_parameters_should_specify_byte_order(self):
        self.assertEqual(pando.model.ByteOrder.BIG_ENDIAN, self.model.parameters["parameter_big_endian"].byte_order)
        self.assertEqual(pando.model.ByteOrder.LITTLE_ENDIAN, self.model.parameters["parameter_little_endian"].byte_order)
        self.assertEqual(pando.model.ByteOrder.LITTLE_ENDIAN, self.model.parameters["enumeration_little_endian"].byte_order)
        self.assertEqual(pando.model.ByteOrder.LITTLE_ENDIAN, self.model.parameters["repeater_little_endian"].byte_order)

if __name__ == '__main__':
    unittest.main()

