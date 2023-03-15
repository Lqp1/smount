import unittest
import pyfakefs.fake_filesystem_unittest
from smount.smount import SerialMounter, MountPoint, MountType

TEST_CONFIG_1 = """
mount_types:
   one:
       mount: echo does nothing
       umount: echo does nothing neither
mounts:
   m_one:
       src: /
       target: /tmp
       type: one
   m_two:
       src: .
       target: /tmp
       type: one
"""

TEST_CONFIG_2 = """
mount_types:
   one:
        mount: echo does nothing
        umount: echo does nothing neither
mounts:
   m_one:
       src: /
       target: /tmp
       type: one
   m_two:
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

class TestMountPoint(pyfakefs.fake_filesystem_unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setUpClassPyfakefs()
        cls.nil_mount_type = MountType("nop", {"mount": "/bin/true", "umount":"/bin/true"})
        cls.fake_fs().create_dir("/one")
        cls.fake_fs().create_file("/one/a")
        cls.fake_fs().create_file("/one/b")
        cls.fake_fs().create_file("/one/c")
        cls.fake_fs().create_dir("/three")

    def test_impossible_mount(self):
        test = MountPoint("test", {"src":"/one/a", "target":"/four"}, self.nil_mount_type)
        self.assertRaises(RuntimeError, test.mount)

    def test_mount(self):
        test = MountPoint("test", {"src":"/one/a", "target":"/three"}, self.nil_mount_type)
        test.mount()

    def test_mount_expanded(self):
        src = "/one/*"
        test = MountPoint("test",
                          {"src":src, "target":"/three", "expand": "last-alpha"},
                          self.nil_mount_type)
        self.assertEqual(test.expand(src), "/one/c")
        self.assertEqual(test.mount(), True)

if __name__ == '__main__':
    unittest.main()
