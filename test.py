import unittest
from smount.smount import SerialMounter

TEST_CONFIG_1 = """
mount_types:
-   one:
        mount: echo does nothing
        umount: echo does nothing neither
mounts:
-   m_one:
        src: /
        target: /tmp
        type: one
-   m_two:
        src: .
        target: /tmp
        type: one
"""

TEST_CONFIG_2 = """
mount_types:
-   one:
        mount: echo does nothing
        umount: echo does nothing neither
mounts:
-   m_one:
        src: /
        target: /tmp
        type: one
-   m_two:
        src: .
        target: /tmp
        type: two
"""

class TestSerialMounter(unittest.TestCase):
    def setUp(self):
        self.instance = SerialMounter([TEST_CONFIG_1])

    def test_ok_list_mounts(self):
        self.assertEqual(len(self.instance.get_mount_points()), 2)

    def test_ko_list_mounts(self):
        #FIXME: Better handle this!
        self.assertRaises(KeyError, SerialMounter, [TEST_CONFIG_2])

    def test_get_config(self):
        mount = self.instance.get('m_one')
        self.assertEqual(mount.name, 'm_one')

if __name__ == '__main__':
    unittest.main()
