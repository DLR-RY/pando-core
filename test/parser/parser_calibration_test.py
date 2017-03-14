
import os
import unittest
import pdoc

class ParserCalibrationTest(unittest.TestCase):

    def setUp(self):
        self.model = self.parseFile("resources/calibration_services.xml")

    def parseFile(self, filename):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", filename)
        parser = pdoc.parser.Parser()
        model = parser.parse(filepath)

        self.assertIsNotNone(model)
        return model

#   def getPacketParameter(self, packet, uid):
#       for p in packet.getParametersAsFlattenedList():
#           if p.uid == uid:
#               return p
#       else:
#           self.fail("Parameter '%s' not found" % uid)
#       return None

    def test_shouldContainCalibrations(self):
        self.assertEqual(4, len(self.model.calibrations))

    def test_shouldContainCalibrationMappings(self):
        self.assertEqual(2, len(self.model.subsystems[0].telemetryCalibrations))
        self.assertEqual(1, len(self.model.subsystems[0].telecommandCalibrations))

    def test_shouldHaveTelecommandParameterCalibration(self):
        packet = self.model.parameters["P7"]
        self.assertEqual("calibration_test", packet.calibration.uid)
        self.assertEqual(True, packet.calibration.extrapolate)
        self.assertEqual(5, len(packet.calibration.points))

        self.assertEqual(0, packet.calibration.points[0].x)
        self.assertEqual(10, packet.calibration.points[0].y)

        self.assertEqual(pdoc.model.Interpolation.UNSIGNED_INTEGER, packet.calibration.inputType)
        self.assertEqual(pdoc.model.Interpolation.UNSIGNED_INTEGER, packet.calibration.outputType)

    def test_shouldHaveTelemetryParameterCalibration(self):
        packet = self.model.parameters["P100"]
        self.assertEqual("calibration_parameter", packet.calibration.uid)
        self.assertEqual(False, packet.calibration.extrapolate)
        self.assertEqual(2, len(packet.calibration.points))

        self.assertEqual(100.12, packet.calibration.points[0].x)
        self.assertEqual(-2, packet.calibration.points[0].y)

        self.assertEqual(pdoc.model.Interpolation.REAL, packet.calibration.inputType)
        self.assertEqual(pdoc.model.Interpolation.SIGNED_INTEGER, packet.calibration.outputType)

    def test_shouldHavePolynomParameterCalibration(self):
        packet = self.model.parameters["P101"]

        self.assertEqual("calibration_polynom", packet.calibration.uid)
        self.assertEqual(1, packet.calibration.a0)
        self.assertEqual(2, packet.calibration.a1)
        self.assertEqual(3.5, packet.calibration.a2)
        self.assertEqual(7, packet.calibration.a3)
        self.assertEqual(100.1, packet.calibration.a4)

    def test_shouldHaveUnmappedCalibrations(self):
        validator = pdoc.model.validator.ModelValidator(self.model)
        additional_tm, unresolved_tm, additional_tc, unresolved_tc = validator.getUnmappedCalibrations()

        self.assertEqual(0, len(additional_tc))
        self.assertEqual(0, len(unresolved_tc))
        self.assertEqual(1, len(additional_tm))
        self.assertEqual(1, len(unresolved_tm))

        self.assertEqual("0201", additional_tm[0].sid)
        self.assertEqual("calibration_polynom2", additional_tm[0].calibration.uid)

        tm, subsystem = unresolved_tm[0]
        self.assertEqual("calibration_polynom", tm.uid)

if __name__ == '__main__':
    unittest.main()
