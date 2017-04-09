#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015-2017, German Aerospace Center (DLR)
#
# This file is part of the development version of the pando library.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Authors:
# - 2015-2017, Fabian Greif (DLR RY-AVS)

import unittest
import logging

import pando


class ModelTest(unittest.TestCase):

    def setUp(self):
        # Store an disable logging for the model
        logger = logging.getLogger('pando.model')
        self.logLevel = logger.getEffectiveLevel()
        logger.setLevel(logging.CRITICAL)

    def tearDown(self):
        # Restore previous log level
        logger = logging.getLogger('pando.model')
        logger.setLevel(self.logLevel)

    def _create_parameter(self, name, model):
        p = pando.model.Parameter(name=name, uid=name.lower(), description=None, parameter_type=None)
        model.parameters[p.uid] = p
        return p

    def _create_repeater(self, name, model):
        p = pando.model.Repeater(name=name, uid=name.lower(), description=None, parameter_type=None)
        model.parameters[p.uid] = p
        return p

    def _generate_packet(self, model):
        packet = pando.model.Packet(name="Test", uid="test", description="",
                                   packet_type=pando.model.Packet.TELECOMMAND)

        packet.append_parameter(self._create_parameter("P1", model))

        repeater = self._create_repeater("P2", model)
        repeater.append_parameter(self._create_parameter("P3", model))

        packet.append_parameter(repeater)
        packet.append_parameter(self._create_parameter("P4", model))

        model.telecommands[packet.uid] = packet
        return packet

    def _generate_packet_with_nested_repeaters(self, model):
        packet = pando.model.Packet(name="Test", uid="test", description="",
                                   packet_type=pando.model.Packet.TELECOMMAND)

        packet.append_parameter(self._create_parameter("P1", model))

        repeater = self._create_repeater("G1", model)
        repeater.append_parameter(self._create_parameter("P2", model))

        repeater2 = self._create_repeater("G2", model)
        repeater2.append_parameter(self._create_parameter("P3", model))
        repeater2.append_parameter(self._create_parameter("P4", model))

        repeater.append_parameter(repeater2)
        packet.append_parameter(repeater)
        packet.append_parameter(self._create_parameter("P5", model))

        model.telecommands[packet.uid] = packet
        return packet

    def test_should_flatten_parameters(self):
        m = pando.model.Model()
        packet = self._generate_packet(m)

        parameters = packet.get_parameters_as_flattened_list()
        self.assertIsNotNone(parameters)

        self.assertEqual(len(parameters), 4)
        self.assertEqual(parameters[0].uid, "p1")
        self.assertEqual(parameters[1].uid, "p2")
        self.assertEqual(parameters[2].uid, "p3")
        self.assertEqual(parameters[3].uid, "p4")

    def test_should_have_correct_repeater_member_count(self):
        model = pando.model.Model()
        packet = self._generate_packet(model)

        parameters = packet.get_parameters_as_flattened_list()
        self.assertEqual(parameters[1].get_flattened_member_count(), 1)

        packet2 = self._generate_packet_with_nested_repeaters(model)

        parameters2 = packet2.get_parameters_as_flattened_list()
        self.assertEqual(parameters2[1].get_flattened_member_count(), 4)
        self.assertEqual(parameters2[3].get_flattened_member_count(), 2)
