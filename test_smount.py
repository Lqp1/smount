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

TEST_CONFIG_VARIABLES = """
variables:
    global_var: "global_value"
    prompt_var: "prompt:Enter prompt value: "
mount_types:
    one:
        mount: "echo $global_var $local_var $prompt_var $src $target"
        umount: "echo $global_var $local_var $prompt_var $src $target"
mounts:
    m_one:
        src: "/one/$local_var"
        target: "/three"
        type: one
        variables:
            local_var: "local_value"
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
        cls.nil_mount_type = MountType("nop", {"mount": "true", "umount":"true"})
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

    def test_mount_logging(self):
        test = MountPoint("test_log", {"src":"/one/a", "target":"/three"}, self.nil_mount_type)
        with self.assertLogs('smount', level='INFO') as log_capture:
            test.mount()
        self.assertTrue(any("Mounting type 'nop'" in log for log in log_capture.output))

    def test_mount_expanded(self):
        src = "/one/*"
        test = MountPoint("test",
                          {"src":src, "target":"/three", "expand": "last-alpha"},
                          self.nil_mount_type)
        self.assertEqual(test.expand(src), "/one/c")
        self.assertEqual(test.mount(), True)

class TestVariables(pyfakefs.fake_filesystem_unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setUpClassPyfakefs()
        cls.fake_fs().create_dir("/one")
        cls.fake_fs().create_file("/one/local_value")
        cls.fake_fs().create_dir("/three")

    def test_variables_prompt(self):
        # pylint: disable=protected-access
        mounter = SerialMounter([TEST_CONFIG_VARIABLES])
        mount = mounter.get('m_one')
        self.assertIsNotNone(mount)
        self.assertEqual(mount.variables.get('global_var'), 'global_value')
        self.assertEqual(mount.variables.get('local_var'), 'local_value')
        self.assertEqual(mount.variables.get('prompt_var'), 'prompt:Enter prompt value: ')

        prompts = []
        def mock_prompter(prompt):
            prompts.append(prompt)
            return "prompted_value"

        self.assertEqual(mount._resolved_cache, {})

        resolved = mount.resolve_variables(mock_prompter, prompt_fallback=False)
        self.assertEqual(resolved.get('global_var'), 'global_value')
        self.assertEqual(resolved.get('local_var'), 'local_value')
        self.assertNotIn('prompt_var', resolved)
        self.assertEqual(prompts, [])

        resolved_all = mount.resolve_variables(mock_prompter, prompt_fallback=True)
        self.assertEqual(resolved_all.get('global_var'), 'global_value')
        self.assertEqual(resolved_all.get('local_var'), 'local_value')
        self.assertEqual(resolved_all.get('prompt_var'), 'prompted_value')
        self.assertEqual(prompts, ['Enter prompt value: '])

        self.assertEqual(mount._resolved_cache.get('prompt_var'), 'prompted_value')
        self.assertEqual(mount.get_resolved_src(resolved_all), '/one/local_value')
        self.assertEqual(mount.get_resolved_target(resolved_all), '/three')

if __name__ == '__main__':
    unittest.main()
