
import os
import unittest
import pdoc

class ParserTest(unittest.TestCase):

    def parse_file(self, filename):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)
        parser = pdoc.parser.Parser()
        model = parser.parse(filepath)

        self.assertIsNotNone(model)
        return model

    def test_should_merge_two_services_with_same_name(self):
        model = self.parse_file("resources/service_with_same_name.xml")

        self.assertTrue("test1" in model.telecommands)
        self.assertTrue("test2" in model.telecommands)

if __name__ == '__main__':
    unittest.main()
