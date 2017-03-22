
import unittest
import logging

import pdoc
import pdoc.model.validator

class ModelTest(unittest.TestCase):

    def setUp(self):
        # Store an disable logging for the model
        logger = logging.getLogger('pdoc.model.validator')
        self.logLevel = logger.getEffectiveLevel()
        logger.setLevel(logging.CRITICAL)

    def tearDown(self):
        # Restore previous log level
        logger = logging.getLogger('pdoc.model.validator')
        logger.setLevel(self.logLevel)

    def _create_parameter(self, name, model):
        p = pdoc.model.Parameter(name=name, uid=name.lower(), description=None, parameter_type=None)
        model.parameters[p.uid] = p
        return p

    def _create_repeater(self, name, model):
        p = pdoc.model.Repeater(name=name, uid=name.lower(), description=None, parameter_type=None)
        model.parameters[p.uid] = p
        return p

    def _generate_packet(self, model):
        packet = pdoc.model.Packet(name="Test", uid="test", description="",
                                   packet_type=pdoc.model.Packet.TELECOMMAND)

        packet.appendParameter(self._create_parameter("P1", model))

        repeater = self._create_repeater("P2", model)
        repeater.appendParameter(self._create_parameter("P3", model))

        packet.appendParameter(repeater)
        packet.appendParameter(self._create_parameter("P4", model))

        model.telecommands[packet.uid] = packet
        return packet

    def _generate_packet_with_nested_repeaters(self, model):
        packet = pdoc.model.Packet(name="Test", uid="test", description="",
                                   packet_type=pdoc.model.Packet.TELECOMMAND)

        packet.appendParameter(self._create_parameter("P1", model))

        repeater = self._create_repeater("G1", model)
        repeater.appendParameter(self._create_parameter("P2", model))

        repeater2 = self._create_repeater("G2", model)
        repeater2.appendParameter(self._create_parameter("P3", model))
        repeater2.appendParameter(self._create_parameter("P4", model))

        repeater.appendParameter(repeater2)
        packet.appendParameter(repeater)
        packet.appendParameter(self._create_parameter("P5", model))

        model.telecommands[packet.uid] = packet
        return packet


    def test_should_verify_paket_mapping_is_complete(self):
        model = pdoc.model.Model()
        self._generate_packet(model)

        subsystem = model.getOrAddSubsystem(0, name="test")
        subsystem.applications[0] = pdoc.model.ApplicationMapping(name="A1", apid=0, description="")
        subsystem.applications[0].appendTelecommand(pdoc.model.TelecommandMapping("test", model.telecommands["test"]))

        subsystem.telecommandParameters["p1"] = pdoc.model.ParameterMapping(sid="s1", parameter=model.parameters["p1"])
        subsystem.telecommandParameters["p2"] = pdoc.model.ParameterMapping(sid="s2", parameter=model.parameters["p2"])
        subsystem.telecommandParameters["p3"] = pdoc.model.ParameterMapping(sid="s3", parameter=model.parameters["p3"])
        subsystem.telecommandParameters["p4"] = pdoc.model.ParameterMapping(sid="s4", parameter=model.parameters["p4"])

        validator = pdoc.model.validator.ModelValidator(model)
        self.assertEqual(len(validator.getUnmappedTelecommandParameters()), 0)

    def test_should_fail_mapping_check_if_is_not_complete(self):
        model = pdoc.model.Model()
        self._generate_packet(model)

        subsystem = model.getOrAddSubsystem(0, name="test")
        subsystem.applications[0] = pdoc.model.ApplicationMapping(name="A1", apid=0, description="")
        subsystem.applications[0].appendTelecommand(pdoc.model.TelecommandMapping("test", model.telecommands["test"]))

        subsystem.telecommandParameters["p1"] = pdoc.model.ParameterMapping(sid="s1", parameter=model.parameters["p1"])
        subsystem.telecommandParameters["p2"] = pdoc.model.ParameterMapping(sid="s2", parameter=model.parameters["p2"])
        subsystem.telecommandParameters["p3"] = pdoc.model.ParameterMapping(sid="s3", parameter=model.parameters["p3"])

        validator = pdoc.model.validator.ModelValidator(model)
        self.assertEqual(len(validator.getUnmappedTelecommandParameters()), 1)

    def test_should_be_fine_if_parameter_mapping_has_too_many_elements(self):
        model = pdoc.model.Model()
        self._generate_packet(model)

        subsystem = model.getOrAddSubsystem(0, name="test")
        subsystem.applications[0] = pdoc.model.ApplicationMapping(name="A1", apid=0, description="")
        subsystem.applications[0].appendTelecommand(pdoc.model.TelecommandMapping("test", model.telecommands["test"]))

        subsystem.telecommandParameters["p1"] = pdoc.model.ParameterMapping(sid="s1", parameter=model.parameters["p1"])
        subsystem.telecommandParameters["p2"] = pdoc.model.ParameterMapping(sid="s2", parameter=model.parameters["p2"])
        subsystem.telecommandParameters["p3"] = pdoc.model.ParameterMapping(sid="s3", parameter=model.parameters["p3"])
        subsystem.telecommandParameters["p4"] = pdoc.model.ParameterMapping(sid="s4", parameter=model.parameters["p4"])
        subsystem.telecommandParameters["p5"] = pdoc.model.ParameterMapping(sid="s5", parameter=model.parameters["p4"])

        validator = pdoc.model.validator.ModelValidator(model)
        self.assertEqual(len(validator.getUnmappedTelecommandParameters()), 0)
