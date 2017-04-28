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
import pando.model.validator

class ModelTest(unittest.TestCase):

    def setUp(self):
        # Store an disable logging for the model
        logger = logging.getLogger('pando.model.validator')
        self.logLevel = logger.getEffectiveLevel()
        logger.setLevel(logging.CRITICAL)

    def tearDown(self):
        # Restore previous log level
        logger = logging.getLogger('pando.model.validator')
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


    def test_should_verify_paket_mapping_is_complete(self):
        model = pando.model.Model()
        self._generate_packet(model)

        subsystem = model.get_or_add_subsystem(0, name="test")
        subsystem.applications[0] = pando.model.ApplicationMapping(name="A1", apid=0, description="")
        subsystem.applications[0].append_telecommand(pando.model.TelecommandMapping("test", model.telecommands["test"]))

        subsystem.telecommand_parameters["p1"] = pando.model.ParameterMapping(sid="s1", parameter=model.parameters["p1"])
        subsystem.telecommand_parameters["p2"] = pando.model.ParameterMapping(sid="s2", parameter=model.parameters["p2"])
        subsystem.telecommand_parameters["p3"] = pando.model.ParameterMapping(sid="s3", parameter=model.parameters["p3"])
        subsystem.telecommand_parameters["p4"] = pando.model.ParameterMapping(sid="s4", parameter=model.parameters["p4"])

        validator = pando.model.validator.ModelValidator(model)
        self.assertEqual(len(validator.get_unmapped_telecommand_parameters()), 0)

    def test_should_fail_mapping_check_if_is_not_complete(self):
        model = pando.model.Model()
        self._generate_packet(model)

        subsystem = model.get_or_add_subsystem(0, name="test")
        subsystem.applications[0] = pando.model.ApplicationMapping(name="A1", apid=0, description="")
        subsystem.applications[0].append_telecommand(pando.model.TelecommandMapping("test", model.telecommands["test"]))

        subsystem.telecommand_parameters["p1"] = pando.model.ParameterMapping(sid="s1", parameter=model.parameters["p1"])
        subsystem.telecommand_parameters["p2"] = pando.model.ParameterMapping(sid="s2", parameter=model.parameters["p2"])
        subsystem.telecommand_parameters["p3"] = pando.model.ParameterMapping(sid="s3", parameter=model.parameters["p3"])

        validator = pando.model.validator.ModelValidator(model)
        self.assertEqual(len(validator.get_unmapped_telecommand_parameters()), 1)

    def test_should_be_fine_if_parameter_mapping_has_too_many_elements(self):
        model = pando.model.Model()
        self._generate_packet(model)

        subsystem = model.get_or_add_subsystem(0, name="test")
        subsystem.applications[0] = pando.model.ApplicationMapping(name="A1", apid=0, description="")
        subsystem.applications[0].append_telecommand(pando.model.TelecommandMapping("test", model.telecommands["test"]))

        subsystem.telecommand_parameters["p1"] = pando.model.ParameterMapping(sid="s1", parameter=model.parameters["p1"])
        subsystem.telecommand_parameters["p2"] = pando.model.ParameterMapping(sid="s2", parameter=model.parameters["p2"])
        subsystem.telecommand_parameters["p3"] = pando.model.ParameterMapping(sid="s3", parameter=model.parameters["p3"])
        subsystem.telecommand_parameters["p4"] = pando.model.ParameterMapping(sid="s4", parameter=model.parameters["p4"])
        subsystem.telecommand_parameters["p5"] = pando.model.ParameterMapping(sid="s5", parameter=model.parameters["p4"])

        validator = pando.model.validator.ModelValidator(model)
        self.assertEqual(len(validator.get_unmapped_telecommand_parameters()), 0)

    def test_should_detect_enumerations_with_non_unique_entries(self):
        model = pando.model.Model()

        enumeration1 = pando.model.Enumeration("Test", "test", 8, "")
        enumeration1.append_entry(pando.model.EnumerationEntry("entry1", 1, ""))
        enumeration1.append_entry(pando.model.EnumerationEntry("entry2", 1, ""))
        model.enumerations[enumeration1.uid] = enumeration1

        enumeration2 = pando.model.Enumeration("Test2", "test2", 8, "")
        enumeration2.append_entry(pando.model.EnumerationEntry("entry1", 1, ""))
        enumeration2.append_entry(pando.model.EnumerationEntry("entry2", 2, ""))
        model.enumerations[enumeration2.uid] = enumeration2

        validator = pando.model.validator.ModelValidator(model)

        enumerations = validator.get_enumeration_with_non_unqiue_values()
        self.assertEqual(len(enumerations), 1)
        self.assertIn(enumeration1, enumerations)
