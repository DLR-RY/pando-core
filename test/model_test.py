
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
        p = pdoc.model.Parameter(name=name, uid=name.lower(), description=None, parameter_type=None)
        model.parameters[p.uid] = p
        return p

    def _createRepeater(self, name, model):
        p = pdoc.model.Repeater(name=name, uid=name.lower(), description=None, parameter_type=None)
        model.parameters[p.uid] = p
        return p

    def _generatePacket(self, model):
        packet = pdoc.model.Packet(name="Test", uid="test", description="",
                                   packet_type=pdoc.model.Packet.TELECOMMAND)

        packet.appendParameter(self._createParameter("P1", model))

        repeater = self._createRepeater("P2", model)
        repeater.appendParameter(self._createParameter("P3", model))

        packet.appendParameter(repeater)
        packet.appendParameter(self._createParameter("P4", model))

        model.telecommands[packet.uid] = packet
        return packet

    def _generatePacketWithNestedRepeaters(self, model):
        packet = pdoc.model.Packet(name="Test", uid="test", description="",
                                   packet_type=pdoc.model.Packet.TELECOMMAND)

        packet.appendParameter(self._createParameter("P1", model))

        repeater = self._createRepeater("G1", model)
        repeater.appendParameter(self._createParameter("P2", model))

        repeater2 = self._createRepeater("G2", model)
        repeater2.appendParameter(self._createParameter("P3", model))
        repeater2.appendParameter(self._createParameter("P4", model))

        repeater.appendParameter(repeater2)
        packet.appendParameter(repeater)
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

    def test_shouldHaveCorrectRepeaterMemberCount(self):
        model = pdoc.model.Model()
        packet = self._generatePacket(model)

        parameters = packet.getParametersAsFlattenedList()
        self.assertEqual(parameters[1].getFlattenedMemberCount(), 1)

        packet2 = self._generatePacketWithNestedRepeaters(model)

        parameters2 = packet2.getParametersAsFlattenedList()
        self.assertEqual(parameters2[1].getFlattenedMemberCount(), 4)
        self.assertEqual(parameters2[3].getFlattenedMemberCount(), 2)
