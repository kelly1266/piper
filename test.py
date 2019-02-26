import unittest
from helper_methods import is_int


class TestIsNumber(unittest.TestCase):

    def test_letter(self):
        self.assertFalse(is_int('s'))

    def test_zero_str(self):
        self.assertTrue(is_int('0'))

    def test_zero_int(self):
        self.assertTrue(is_int(0))

    def test_negative_str(self):
        self.assertTrue(is_int('-32'))

    def test_negative_int(self):
        self.assertTrue(is_int(-32))

    def test_positive_str(self):
        self.assertTrue(is_int('32'))

    def test_positive_int(self):
        self.assertTrue(is_int(32))


if __name__ == '__main__':
    unittest.main()