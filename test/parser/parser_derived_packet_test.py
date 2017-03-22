
import os
import datetime
import unittest

import pdoc

class ParserTest(unittest.TestCase):

    def setUp(self):
        self.model = self.parse_file("resources/derived_packet.xml")

    def parse_file(self, filename):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", filename)
        parser = pdoc.parser.Parser()
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
