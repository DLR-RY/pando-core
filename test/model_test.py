
import unittest
import logging

import pdoc

class ModelTest(unittest.TestCase):

    def setUp(self):
        # Store an disable logging for the model
        logger = logging.getLogger('pdoc.model')
        self.logLevel = logger.getEffectiveLevel()
        logger.setLevel(logging.CRITICAL)

    def tearDown(self):
        # Restore previous log level
        logger = logging.getLogger('pdoc.model')
        logger.setLevel(self.logLevel)

    def _createParameter(self, name, model):
        p = pdoc.model.Parameter(name=name, uid=name.lower(), description=None, parameterType=None)
        model.parameters[p.uid] = p
        return p

    def _createGroup(self, name, model):
        p = pdoc.model.Group(name=name, uid=name.lower(), description=None, parameterType=None)
        model.parameters[p.uid] = p
        return p

    def _generatePacket(self, model):
        packet = pdoc.model.Packet(name="Test", uid="test", description="")

        packet.appendParameter(self._createParameter("P1", model))

        group = self._createGroup("P2", model)
        group.appendParameter(self._createParameter("P3", model))

        packet.appendParameter(group)
        packet.appendParameter(self._createParameter("P4", model))

        model.telecommands[packet.uid] = packet
        return packet

    def _generatePacketWithNestedGroups(self, model):
        packet = pdoc.model.Packet(name="Test", uid="test", description="")

        packet.appendParameter(self._createParameter("P1", model))

        group = self._createGroup("G1", model)
        group.appendParameter(self._createParameter("P2", model))

        group2 = self._createGroup("G2", model)
        group2.appendParameter(self._createParameter("P3", model))
        group2.appendParameter(self._createParameter("P4", model))

        group.appendParameter(group2)
        packet.appendParameter(group)
        packet.appendParameter(self._createParameter("P5", model))

        model.telecommands[packet.uid] = packet
        return packet

    def test_shouldFlattenParameters(self):
        m = pdoc.model.Model()
        packet = self._generatePacket(m)

        parameters = packet.getParametersAsFlattenedList()
        self.assertIsNotNone(parameters)

        self.assertEqual(len(parameters), 4)
        self.assertEqual(parameters[0].uid, "p1")
        self.assertEqual(parameters[1].uid, "p2")
        self.assertEqual(parameters[2].uid, "p3")
        self.assertEqual(parameters[3].uid, "p4")

    def test_shouldVerifyPaketMappingIsComplete(self):
        model = pdoc.model.Model()
        self._generatePacket(model)

        subsystem = model.getOrAddSubsystem(0)
        subsystem.applications[0] = pdoc.model.ApplicationMapping(name="A1", apid=0, description="")
        subsystem.applications[0].appendTelecommand(pdoc.model.TelecommandMapping("test", model.telecommands["test"]))

        subsystem.telecommandParameters["p1"] = pdoc.model.ParameterMapping(sid="s1", parameter=model.parameters["p1"])
        subsystem.telecommandParameters["p2"] = pdoc.model.ParameterMapping(sid="s2", parameter=model.parameters["p2"])
        subsystem.telecommandParameters["p3"] = pdoc.model.ParameterMapping(sid="s3", parameter=model.parameters["p3"])
        subsystem.telecommandParameters["p4"] = pdoc.model.ParameterMapping(sid="s4", parameter=model.parameters["p4"])

        self.assertEqual(len(model.getUnmappedTelecommandParameters()), 0)

    def test_shouldFailMappingCheckIfIsNotComplete(self):
        model = pdoc.model.Model()
        self._generatePacket(model)

        subsystem = model.getOrAddSubsystem(0)
        subsystem.applications[0] = pdoc.model.ApplicationMapping(name="A1", apid=0, description="")
        subsystem.applications[0].appendTelecommand(pdoc.model.TelecommandMapping("test", model.telecommands["test"]))

        subsystem.telecommandParameters["p1"] = pdoc.model.ParameterMapping(sid="s1", parameter=model.parameters["p1"])
        subsystem.telecommandParameters["p2"] = pdoc.model.ParameterMapping(sid="s2", parameter=model.parameters["p2"])
        subsystem.telecommandParameters["p3"] = pdoc.model.ParameterMapping(sid="s3", parameter=model.parameters["p3"])

        self.assertEqual(len(model.getUnmappedTelecommandParameters()), 1)

    def test_shouldBeFineIfParameterMappingHasToManyElements(self):
        model = pdoc.model.Model()
        self._generatePacket(model)

        subsystem = model.getOrAddSubsystem(0)
        subsystem.applications[0] = pdoc.model.ApplicationMapping(name="A1", apid=0, description="")
        subsystem.applications[0].appendTelecommand(pdoc.model.TelecommandMapping("test", model.telecommands["test"]))

        subsystem.telecommandParameters["p1"] = pdoc.model.ParameterMapping(sid="s1", parameter=model.parameters["p1"])
        subsystem.telecommandParameters["p2"] = pdoc.model.ParameterMapping(sid="s2", parameter=model.parameters["p2"])
        subsystem.telecommandParameters["p3"] = pdoc.model.ParameterMapping(sid="s3", parameter=model.parameters["p3"])
        subsystem.telecommandParameters["p4"] = pdoc.model.ParameterMapping(sid="s4", parameter=model.parameters["p4"])
        subsystem.telecommandParameters["p5"] = pdoc.model.ParameterMapping(sid="s5", parameter=model.parameters["p4"])

        self.assertEqual(len(model.getUnmappedTelecommandParameters()), 0)

    def test_shouldHaveCorrectGroupMemberCount(self):
        model = pdoc.model.Model()
        packet = self._generatePacket(model)

        parameters = packet.getParametersAsFlattenedList()
        self.assertEqual(parameters[1].getFlattenedGroupMemberCount(), 1)

        packet2 = self._generatePacketWithNestedGroups(model)

        parameters2 = packet2.getParametersAsFlattenedList()
        self.assertEqual(parameters2[1].getFlattenedGroupMemberCount(), 4)
        self.assertEqual(parameters2[3].getFlattenedGroupMemberCount(), 2)
