import glob
import itertools
import logging
import os
import string
import subprocess
import yaml

logger = logging.getLogger("smount")

class MountType:
    def __init__(self, name: str, config: dict):
        self._config = config
        self.name = name

    @property
    def config(self) -> dict:
        return self._config

    def mount(self, src: str, target: str, variables: dict = None) -> bool:
        cmd_template = string.Template(self._config['mount'])
        args = self.__args(src, target)
        if variables:
            args.update(variables)
        cmd = cmd_template.substitute(**args)
        logger.info("Mounting type '%s': src='%s', target='%s'", self.name, src, target)
        logger.debug("Running command: %s", cmd)
        success = self.__run(cmd)
        if success:
            logger.info("Successfully mounted type '%s'", self.name)
        else:
            logger.error("Failed to mount type '%s': command exited with non-zero code", self.name)
        return success

    def unmount(self, src: str, target: str, variables: dict = None) -> bool:
        cmd_template = string.Template(self._config['umount'])
        args = self.__args(src, target)
        if variables:
            args.update(variables)
        cmd = cmd_template.substitute(**args)
        logger.info("Unmounting type '%s': src='%s', target='%s'", self.name, src, target)
        logger.debug("Running command: %s", cmd)
        success = self.__run(cmd)
        if success:
            logger.info("Successfully unmounted type '%s'", self.name)
        else:
            logger.error("Failed to unmount type '%s': command exited with non-zero code",
                         self.name)
        return success

    @staticmethod
    def __args(src: str, target: str) -> dict:
        return {
            'src': src,
            'target': target,
            'uid': os.getuid(),
            'gid': os.getgid(),
            'login': os.getlogin()
        }

    @staticmethod
    def __run(cmd: str) -> bool:
        return os.system(cmd) == 0


class MountPoint:
    BUILTIN_VARIABLES = {'src', 'target', 'uid', 'gid', 'login'}

    def __init__(self, name: str, config: dict, mean: MountType,
                 variables: dict = None, prompter = None):
        self._config = config
        self._mean = mean
        self.name = name
        self.variables = variables if variables is not None else {}
        self.prompter = prompter if prompter is not None else input
        self._resolved_cache = {}

    def _get_referenced_variables(self) -> set:
        referenced = set()
        referenced.update(self._find_template_variables(self._config.get('src', '')))
        referenced.update(self._find_template_variables(self._config.get('target', '')))
        if self._mean:
            referenced.update(self._find_template_variables(self._mean.config.get('mount', '')))
            referenced.update(self._find_template_variables(self._mean.config.get('umount', '')))
        return referenced

    @staticmethod
    def _find_template_variables(template_str: str) -> set:
        if not template_str:
            return set()
        t = string.Template(template_str)
        variables = set()
        for match in t.pattern.finditer(template_str):
            name = match.group('named') or match.group('braced')
            if name:
                variables.add(name)
        return variables

    def resolve_variables(self, prompter=None, prompt_fallback=True) -> dict:
        if prompter is None:
            prompter = self.prompter

        referenced = self._get_referenced_variables()
        resolved = {}

        for var in referenced:
            if var in self.BUILTIN_VARIABLES:
                continue

            # Check cache
            if var in self._resolved_cache:
                resolved[var] = self._resolved_cache[var]
                continue

            val = self.variables.get(var)
            if val is None:
                if not prompt_fallback:
                    continue
                logger.warning(
                    "Variable '%s' is not defined in config. Prompting as fallback.",
                    var
                )
                prompt_str = f"Enter value for {var}: "
                val_input = prompter(prompt_str)
                self._resolved_cache[var] = val_input
                resolved[var] = val_input
                continue

            if val == "prompt":
                if not prompt_fallback:
                    continue
                prompt_str = f"Enter value for {var}: "
                val_input = prompter(prompt_str)
                self._resolved_cache[var] = val_input
                resolved[var] = val_input
            elif isinstance(val, str) and val.startswith("prompt:"):
                if not prompt_fallback:
                    continue
                prompt_str = val[len("prompt:"):]
                val_input = prompter(prompt_str)
                self._resolved_cache[var] = val_input
                resolved[var] = val_input
            else:
                resolved[var] = val

        return resolved

    def get_resolved_src(self, resolved_vars: dict) -> str:
        src_tpl = self._config.get('src', '')
        return string.Template(src_tpl).safe_substitute(**resolved_vars)

    def get_resolved_target(self, resolved_vars: dict) -> str:
        target_tpl = self._config.get('target', '')
        return string.Template(target_tpl).safe_substitute(**resolved_vars)

    def expand(self, path: str) -> str:
        expand_type = self._config.get("expand")
        if expand_type is None:
            logger.debug("No expansion defined for '%s', path: '%s'", self.name, path)
            return path
        logger.debug("Expanding path '%s' using type '%s'", path, expand_type)
        if expand_type == 'last-alpha':
            files = [f for f in glob.glob(path) if os.path.isfile(f)]
            if not files:
                logger.warning("No files matched glob '%s' for last-alpha expansion", path)
                return path
            list.sort(files)
            expanded = files[-1]
            logger.debug("Expanded '%s' to '%s'", path, expanded)
            return expanded
        if expand_type == 'last-ctime':
            files = [f for f in glob.glob(path) if os.path.isfile(f)]
            if not files:
                logger.warning("No files matched glob '%s' for last-ctime expansion", path)
                return path
            files.sort(key=os.path.getctime)
            expanded = files[-1]
            logger.debug("Expanded '%s' to '%s'", path, expanded)
            return expanded

        logger.error("Unknown expansion type '%s' for mountpoint '%s'", expand_type, self.name)
        raise RuntimeError("Unknown expansion type")

    def mount(self, prompter=None) -> bool:
        resolved_vars = self.resolve_variables(prompter, prompt_fallback=True)
        target = self.get_resolved_target(resolved_vars)
        logger.debug("Preparing to mount mountpoint '%s' to target '%s'", self.name, target)
        if not os.path.isdir(target):
            logger.error("Target '%s' is not a directory or does not exist for mountpoint '%s'",
                         target, self.name)
            raise RuntimeError(f"{self.name}: target {target} is not ready.")
        src = self.get_resolved_src(resolved_vars)
        src_expanded = self.expand(src)
        return self._mean.mount(src_expanded, target, resolved_vars)

    def unmount(self, prompter=None) -> bool:
        resolved_vars = self.resolve_variables(prompter, prompt_fallback=True)
        target = self.get_resolved_target(resolved_vars)
        logger.debug("Preparing to unmount mountpoint '%s' from target '%s'", self.name, target)
        src = self.get_resolved_src(resolved_vars)
        src_expanded = self.expand(src)
        return self._mean.unmount(src_expanded, target, resolved_vars)

    def ismounted(self) -> bool:
        resolved_vars = self.resolve_variables(prompt_fallback=False)
        target = self.get_resolved_target(resolved_vars)
        if self._find_template_variables(target):
            logger.debug("Target '%s' contains unresolved variables, assuming not mounted", target)
            return False
        logger.debug("Checking if target '%s' is mounted", target)
        try:
            mounts = subprocess.check_output(["mount"]).decode("utf-8").splitlines()
        except subprocess.SubprocessError as e:
            logger.error("Failed to check mount points: %s", e)
            return False
        for i in mounts:
            try:
                mountpoint = i.split(' ')[2]
                if os.path.abspath(mountpoint) == os.path.abspath(target):
                    logger.debug("Target '%s' is mounted", target)
                    return True
            except IndexError:
                continue
        logger.debug("Target '%s' is not mounted", target)
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

    def __init__(self, config=None):
        if config is None:
            self._config = self._parse_files(self.DEFAULT_CONFIG_PATHS)
        else:
            self._config = config

        self._refresh_config()

    @staticmethod
    def _get_files(path: str) -> list[str]:
        logger.debug("Scanning path for configuration files: '%s'", path)
        if os.path.isfile(path):
            logger.debug("Found configuration file: '%s'", path)
            return [path]
        if not os.path.isdir(path):
            logger.debug("Path is not a file or directory: '%s'", path)
            return []
        files = sorted([os.path.join(path, f) for f in os.listdir(
            path) if os.path.isfile(os.path.join(path, f))])
        logger.debug("Found configuration files in directory '%s': %s", path, files)
        return files

    @staticmethod
    def _parse_files(paths: list[str]) -> list[str]:
        logger.debug("Parsing configuration paths: %s", paths)
        files = [SerialMounter._get_files(os.path.expanduser(path)) for path in paths]
        configs = []
        for file in list(itertools.chain(*files)):
            logger.info("Loading configuration file: '%s'", file)
            try:
                with open(file, 'r', encoding="utf-8") as stream:
                    configs.append(stream.read())
            except OSError as e:
                logger.error("Failed to read config file '%s': %s", file, e)
                raise
        return configs

    def _load_types(self):
        for chunk in self._config:
            try:
                parsed = yaml.safe_load(chunk)
                if parsed is None or 'mount_types' not in parsed:
                    continue
                for name, config in parsed['mount_types'].items():
                    logger.debug("Loading mount type '%s' with config: %s", name, config)
                    self._mount_types[name] = MountType(name, config)
            except yaml.YAMLError as exc:
                logger.error("YAML parsing error while loading mount types: %s", exc)
                raise RuntimeError("Could not load config properly: " + str(exc)) from exc

    def _load_variables(self):
        for chunk in self._config:
            try:
                parsed = yaml.safe_load(chunk)
                if parsed is None or 'variables' not in parsed:
                    continue
                for name, value in parsed['variables'].items():
                    logger.debug("Loading global variable '%s': %s", name, value)
                    self._variables[name] = value
            except yaml.YAMLError as exc:
                logger.error("YAML parsing error while loading variables: %s", exc)
                raise RuntimeError("Could not load config properly: " + str(exc)) from exc

    def _load_mounts(self):
        for chunk in self._config:
            try:
                parsed = yaml.safe_load(chunk)
                if parsed is None or 'mounts' not in parsed:
                    continue
                for name, config in parsed['mounts'].items():
                    if config.get('type') not in self._mount_types:
                        logger.error("Mount type '%s' for mountpoint '%s' is not defined",
                                     config.get('type'), name)
                        raise KeyError(config.get('type'))
                    mean = self._mount_types[config['type']]
                    logger.debug("Loading mountpoint '%s' with config: %s", name, config)

                    # Merge global variables with mountpoint-specific variables
                    mount_vars = dict(self._variables)
                    if 'variables' in config:
                        logger.debug("Loading variables for mountpoint '%s': %s",
                                     name, config['variables'])
                        mount_vars.update(config['variables'])

                    self._mount_points.append(
                        MountPoint(name, config, mean, variables=mount_vars))
            except yaml.YAMLError as exc:
                logger.error("YAML parsing error while loading mountpoints: %s", exc)
                raise RuntimeError("Could not load config properly: " + str(exc)) from exc

    def _refresh_config(self) -> None:
        self._mount_types = {}
        self._mount_points = []
        self._variables = {}
        self._load_types()
        self._load_variables()
        self._load_mounts()

    def get_mount_points(self) -> list[MountPoint]:
        return self._mount_points

    def get(self, name: str) -> MountPoint:
        matching = list(filter(lambda x: x.name == name, self._mount_points))
        if len(matching) == 0:
            return None
        return matching[0]
