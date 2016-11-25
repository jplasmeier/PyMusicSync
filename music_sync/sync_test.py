import sync
import unittest

class TestGetClosestIndex(unittest.TestCase):

    def test_closest_index(self):
        boundaries = {0: '3', 257: 'T', 131: 'L', 260: 'V', 263: 'W', 11: 'A', 154: 'M', 31: 'B', 163: 'N', 169: 'O', 47: 'C', 178: 'P', 189: 'R', 62: 'D', 76: 'E', 82: 'F', 213: 'S', 92: 'G', 95: 'H', 99: 'I', 115: 'J', 122: 'K'}
        target_index = 30
        actual = sync.get_closest_index(boundaries, target_index)
        expected = 31
        self.assertEqual(actual, expected)