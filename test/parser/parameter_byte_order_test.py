
import os
import datetime
import unittest

import pdoc

class ParameterByteOrderTest(unittest.TestCase):

    def setUp(self):
        self.model = self.parse_file("resources/parameter_byte_order.xml")

    def parse_file(self, filename):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", filename)
        parser = pdoc.parser.Parser()
        model = parser.parse(filepath)

        self.assertIsNotNone(model)
        return model

    def test_parameters_should_be_big_endian_by_default(self):
        parameter = self.model.parameters["parameter_default"]
        self.assertEqual(pdoc.model.ByteOrder.BIG_ENDIAN, parameter.byte_order)

    def test_parameters_should_specify_byte_order(self):
        self.assertEqual(pdoc.model.ByteOrder.BIG_ENDIAN, self.model.parameters["parameter_big_endian"].byte_order)
        self.assertEqual(pdoc.model.ByteOrder.LITTLE_ENDIAN, self.model.parameters["parameter_little_endian"].byte_order)
        self.assertEqual(pdoc.model.ByteOrder.LITTLE_ENDIAN, self.model.parameters["enumeration_little_endian"].byte_order)
        self.assertEqual(pdoc.model.ByteOrder.LITTLE_ENDIAN, self.model.parameters["repeater_little_endian"].byte_order)

if __name__ == '__main__':
    unittest.main()

