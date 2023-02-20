import glob
import os
import string
import yaml


class MountType:
    def __init__(self, name, config):
        self.config = config
        self.name = name

    def args(self, src, target):
        return {
            'src': src,
            'target': target,
            'uid': os.getuid(),
            'gid': os.getgid(),
            'login': os.getlogin()
        }

    def mount(self, src, target):
        cmd = string.Template(self.config['mount'])
        self.__run(cmd.substitute(**self.args(src, target)))

    def unmount(self, src, target):
        cmd = string.Template(self.config['umount'])
        self.__run(cmd.substitute(**self.args(src, target)))

    def __run(self, cmd):
        os.system(cmd)


class MountPoint:
    def __init__(self, name, config, mean):
        self.config = config
        self.name = name
        self.mean = mean

    def expand(self, path):
        expand_type = self.config.get("expand")
        if expand_type is None:
            return path
        if expand_type == 'last-alpha':
            files = [f for f in glob.glob(path) if os.path.isfile(f)]
            list.sort(files)
            return files[-1]
        if expand_type == 'last-ctime':
            files = [f for f in glob.glob(path) if os.path.isfile(f)]
            files.sort(key=os.path.getctime)
            return files[-1]

        raise RuntimeError("Unknown expansion type")

    def mount(self):
        target = self.config['target']
        if not os.path.isdir(target):
            print(f"{self.name}: target {target} is not ready.")
        self.mean.mount(
            self.expand(self.config['src']),
            target)

    def unmount(self):
        self.mean.unmount(
            self.expand(self.config['src']),
            self.config['target'])

    def ismounted(self):
        mounts = None
        with open("/proc/mounts", "r", encoding="utf-8") as stream:
            mounts = stream.readlines()
        for i in mounts:
            mountpoint = i.split(' ')[1]
            if os.path.abspath(mountpoint) == os.path.abspath(
                    self.config['target']):
                return True
        return False

    def toggle(self):
        if self.ismounted():
            self.unmount()
        else:
            self.mount()

    def __str__(self):
        logstr = f"""
        {self.name} : {self.config['src']} => {self.config['target']} [{self.config['type']}]
        """.strip(" \n")
        if self.ismounted():
            return f"🟢 {logstr}"
        return f"🔴 {logstr}"


class SerialMounter:
    CONFIGS = ["/etc/smount", "~/.config/smount", "~/.smount"]

    def __init__(self):
        self.refresh_config()

    def get_files(self, path):
        if os.path.isfile(path):
            return [path]
        if not os.path.isdir(path):
            return []
        files = sorted([os.path.join(path, f) for f in os.listdir(
            path) if os.path.isfile(os.path.join(path, f))])
        return files

    def load_types(self, _path):
        for path in self.get_files(_path):
            with open(path, 'r', encoding="utf-8") as stream:
                try:
                    config = yaml.safe_load(stream)
                    if 'mount_types' not in config:
                        continue
                    for i in config['mount_types']:
                        name = next(iter(i))
                        self.mount_types[name] = MountType(name, i[name])
                except yaml.YAMLError as exc:
                    print(exc)

    def load_mounts(self, _path):
        for path in self.get_files(_path):
            with open(path, 'r', encoding="utf-8") as stream:
                try:
                    config = yaml.safe_load(stream)
                    if 'mounts' not in config:
                        continue
                    for i in config['mounts']:
                        name = next(iter(i))
                        mean = self.mount_types[i[name]['type']]
                        self.mount_points.append(
                            MountPoint(name, i[name], mean))
                except yaml.YAMLError as exc:
                    print(exc)

    def refresh_config(self):
        self.mount_types = {}
        self.mount_points = []
        for config in self.CONFIGS:
            self.load_types(os.path.expanduser(config))
        for config in self.CONFIGS:
            self.load_mounts(os.path.expanduser(config))

    def get_mount_points(self):
        return self.mount_points

    def get(self, name):
        matching = list(filter(lambda x: x.name == name, self.mount_points))
        if len(matching) == 0:
            return None
        return matching[0]
