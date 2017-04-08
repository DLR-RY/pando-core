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


class ParserTest(unittest.TestCase):

    def setUp(self):
        self.model = self.parse_file("resources/derived_packet.xml")

    def parse_file(self, filename):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", filename)
        parser = pando.parser.Parser()
        model = parser.parse(filepath)

        self.assertIsNotNone(model)
        return model

    def test_should_override_additional_fields(self):
        tm1 = self.model.telemetries["tm1"]
        tm1_d = self.model.telemetries["tm1_d"]

        self.assertIn(['See Also', 'See also text.'], tm1.additional)

        self.assertNotIn(['See Also', 'See also text.'], tm1_d.additional)
        self.assertIn(['See Also', 'Derived see also text.'], tm1_d.additional)


if __name__ == '__main__':
    unittest.main()
