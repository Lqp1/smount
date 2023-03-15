import glob
import os
import string
import itertools
import yaml

class MountType:
    def __init__(self, name: str, config: dict):
        self._config = config
        self.name = name

    def mount(self, src: str, target: str) -> bool:
        cmd = string.Template(self._config['mount'])
        return self.__run(cmd.substitute(**self.__args(src, target)))

    def unmount(self, src:str, target:str) -> bool:
        cmd = string.Template(self._config['umount'])
        return self.__run(cmd.substitute(**self.__args(src, target)))

    @staticmethod
    def __args(src: str, target:str) -> dict:
        return {
            'src': src,
            'target': target,
            'uid': os.getuid(),
            'gid': os.getgid(),
            'login': os.getlogin()
        }

    @staticmethod
    def __run(cmd:str) -> bool:
        return os.system(cmd) == 0


class MountPoint:
    def __init__(self, name: str, config: dict, mean: MountType):
        self._config = config
        self._mean = mean
        self.name = name

    def expand(self, path:str) -> str:
        expand_type = self._config.get("expand")
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
        target = self._config['target']
        if not os.path.isdir(target):
            raise RuntimeError(f"{self.name}: target {target} is not ready.")
        return self._mean.mount(
            self.expand(self._config['src']),
            target)

    def unmount(self) -> bool:
        return self._mean.unmount(
                self.expand(self._config['src']),
                self._config['target'])

    def ismounted(self) -> bool:
        mounts = None
        with open("/proc/mounts", "r", encoding="utf-8") as stream:
            mounts = stream.readlines()
        for i in mounts:
            mountpoint = i.split(' ')[1]
            if os.path.abspath(mountpoint) == os.path.abspath(
                    self._config['target']):
                return True
        return False

    def toggle(self) -> bool:
        if self.ismounted():
            return self.unmount()
        return self.mount()

    def __str__(self):
        logstr = f"""
        {self.name} : {self._config['src']} => {self._config['target']} [{self._config['type']}]
        """.strip(" \n")
        if self.ismounted():
            return f"🟢 {logstr}"
        return f"🔴 {logstr}"


class SerialMounter:
    DEFAULT_CONFIG_PATHS = ["/etc/smount", "~/.config/smount", "~/.smount"]

    def __init__(self, config = None):
        if config is None:
            self._config = self._parse_files(self.DEFAULT_CONFIG_PATHS)
        else:
            self._config = config

        self._refresh_config()

    @staticmethod
    def _get_files(path: str) -> list[str]:
        if os.path.isfile(path):
            return [path]
        if not os.path.isdir(path):
            return []
        files = sorted([os.path.join(path, f) for f in os.listdir(
            path) if os.path.isfile(os.path.join(path, f))])
        return files

    @staticmethod
    def _parse_files(paths: list[str]) -> list[str]:
        files = [ SerialMounter._get_files(os.path.expanduser(path)) for path in paths ]
        configs = []
        for file in list(itertools.chain(*files)):
            with open(file, 'r', encoding="utf-8") as stream:
                configs.append(stream.read())
        return configs

    def _load_types(self):
        for chunk in self._config:
            try:
                parsed = yaml.safe_load(chunk)
                if 'mount_types' not in parsed:
                    continue
                for i in parsed['mount_types']:
                    name = next(iter(i))
                    self._mount_types[name] = MountType(name, i[name])
            except yaml.YAMLError as exc:
                raise RuntimeError("Could not load config properly: " + exc) from exc

    def _load_mounts(self):
        for chunk in self._config:
            try:
                parsed = yaml.safe_load(chunk)
                if 'mounts' not in parsed:
                    continue
                for i in parsed['mounts']:
                    name = next(iter(i))
                    mean = self._mount_types[i[name]['type']]
                    self._mount_points.append(
                        MountPoint(name, i[name], mean))
            except yaml.YAMLError as exc:
                raise RuntimeError("Could not load config properly: " + exc) from exc

    def _refresh_config(self) -> None:
        self._mount_types = {}
        self._mount_points = []
        self._load_types()
        self._load_mounts()

    def get_mount_points(self) -> list[MountPoint]:
        return self._mount_points

    def get(self, name:str) -> MountPoint:
        matching = list(filter(lambda x: x.name == name, self._mount_points))
        if len(matching) == 0:
            return None
        return matching[0]
