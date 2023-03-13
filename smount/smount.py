import glob
import os
import string
import itertools
import yaml

class MountType:
    def __init__(self, name: str, config: dict):
        self.config = config
        self.name = name

    def args(self, src: str, target:str) -> dict:
        return {
            'src': src,
            'target': target,
            'uid': os.getuid(),
            'gid': os.getgid(),
            'login': os.getlogin()
        }

    def mount(self, src: str, target: str) -> bool:
        cmd = string.Template(self.config['mount'])
        return self.__run(cmd.substitute(**self.args(src, target)))

    def unmount(self, src:str, target:str) -> bool:
        cmd = string.Template(self.config['umount'])
        return self.__run(cmd.substitute(**self.args(src, target)))

    def __run(self, cmd:str) -> bool:
        return os.system(cmd) == 0


class MountPoint:
    def __init__(self, name: str, config: dict, mean: MountType):
        self.config = config
        self.name = name
        self.mean = mean

    def expand(self, path:str) -> str:
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

    def mount(self) -> bool:
        target = self.config['target']
        if not os.path.isdir(target):
            raise RuntimeError(f"{self.name}: target {target} is not ready.")
        return self.mean.mount(
            self.expand(self.config['src']),
            target)

    def unmount(self) -> bool:
        return self.mean.unmount(
                self.expand(self.config['src']),
                self.config['target'])

    def ismounted(self) -> bool:
        mounts = None
        with open("/proc/mounts", "r", encoding="utf-8") as stream:
            mounts = stream.readlines()
        for i in mounts:
            mountpoint = i.split(' ')[1]
            if os.path.abspath(mountpoint) == os.path.abspath(
                    self.config['target']):
                return True
        return False

    def toggle(self) -> bool:
        if self.ismounted():
            return self.unmount()
        return self.mount()

    def __str__(self):
        logstr = f"""
        {self.name} : {self.config['src']} => {self.config['target']} [{self.config['type']}]
        """.strip(" \n")
        if self.ismounted():
            return f"🟢 {logstr}"
        return f"🔴 {logstr}"


class SerialMounter:
    DEFAULT_CONFIG_PATHS = ["/etc/smount", "~/.config/smount", "~/.smount"]

    def __init__(self, config = None):
        if config is None:
            self.config = self.parse_files(self.DEFAULT_CONFIG_PATHS)
        else:
            self.config = config

        self.refresh_config()

    def get_files(self, path: str) -> list[str]:
        if os.path.isfile(path):
            return [path]
        if not os.path.isdir(path):
            return []
        files = sorted([os.path.join(path, f) for f in os.listdir(
            path) if os.path.isfile(os.path.join(path, f))])
        return files

    def parse_files(self, paths: list[str]) -> list[str]:
        files = [ self.get_files(os.path.expanduser(path)) for path in paths ]
        configs = []
        for file in list(itertools.chain(*files)):
            with open(file, 'r', encoding="utf-8") as stream:
                configs.append(stream.read())
        return configs

    def load_types(self):
        for chunk in self.config:
            try:
                parsed = yaml.safe_load(chunk)
                if 'mount_types' not in parsed:
                    continue
                for i in parsed['mount_types']:
                    name = next(iter(i))
                    self.mount_types[name] = MountType(name, i[name])
            except yaml.YAMLError as exc:
                raise RuntimeError("Could not load config properly: " + exc) from exc

    def load_mounts(self):
        for chunk in self.config:
            try:
                parsed = yaml.safe_load(chunk)
                if 'mounts' not in parsed:
                    continue
                for i in parsed['mounts']:
                    name = next(iter(i))
                    mean = self.mount_types[i[name]['type']]
                    self.mount_points.append(
                        MountPoint(name, i[name], mean))
            except yaml.YAMLError as exc:
                raise RuntimeError("Could not load config properly: " + exc) from exc

    def refresh_config(self) -> None:
        self.mount_types = {}
        self.mount_points = []
        self.load_types()
        self.load_mounts()

    def get_mount_points(self) -> list[MountPoint]:
        return self.mount_points

    def get(self, name:str) -> MountPoint:
        matching = list(filter(lambda x: x.name == name, self.mount_points))
        if len(matching) == 0:
            return None
        return matching[0]
