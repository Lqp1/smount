#!/usr/bin/env python

import yaml
import string
import os
import sys
import re

class MountType:
    def __init__(self, name, config):
        self.config = config
        self.name = name

    def mount(self, src, target):
        cmd = string.Template(self.config['mount'])
        self.__run(cmd.substitute(src=src, target=target))

    def unmount(self, src, target):
        cmd = string.Template(self.config['umount'])
        self.__run(cmd.substitute(src=src, target=target))

    def __run(self, cmd):
        os.system(cmd)

class MountPoint:
    def __init__(self, name, config, mean):
        self.config = config
        self.name = name
        self.mean = mean

    def mount(self):
        target = self.config['target']
        if not os.path.isdir(target):
            print(f"{self.name}: target {target} is not ready.")
        self.mean.mount(self.config['src'], target)

    def unmount(self):
        self.mean.unmount(self.config['src'], self.config['target'])

    def ismounted(self):
        mounts = None
        with open("/proc/mounts", "r") as stream:
            mounts = stream.readlines()
        for i in mounts:
            if len(re.findall(f" {self.config['target']} ", i.strip())) >= 1:
                return True
        return False

    def toggle(self):
        if self.ismounted():
            self.unmount()
        else:
            self.mount()

    def __str__(self):
        s = f"{self.name} : {self.config['src']} => {self.config['target']} [{self.config['type']}]"
        if self.ismounted():
            return f"🟢 {s}"
        else:
            return f"🔴 {s}"

class SerialMounter:
    CONFIGS = ["/etc/smount", "~/.config/smount", "~/.smount", "config/mounts.yml"]

    def __init__(self):
        self.refresh_config()

    def get_files(self, path):
        if os.path.isfile(path):
            return [path]
        if not os.path.isdir(path):
            return []
        return [f for f in os.listdir(path) if os.path.isfile(os.join(path, f))].sort()

    def load_types(self, _path):
        for path in self.get_files(_path):
            with open(path, 'r') as stream:
                try:
                    config = yaml.safe_load(stream)
                    for i in config['mount_types']:
                        name = next(iter(i))
                        self.mount_types[name] = MountType(name, i[name])
                except yaml.YAMLError as exc:
                    print(exc)

    def load_mounts(self, _path):
        for path in self.get_files(_path):
            with open(path, 'r') as stream:
                try:
                    config = yaml.safe_load(stream)
                    for i in config['mounts']:
                        name = next(iter(i))
                        mean = self.mount_types[i[name]['type']]
                        self.mount_points.append(MountPoint(name, i[name], mean))
                except yaml.YAMLError as exc:
                    print(exc)

    def refresh_config(self):
        self.mount_types = {}
        self.mount_points = []
        for config in self.CONFIGS:
            self.load_types(config)
        for config in self.CONFIGS:
            self.load_mounts(config)

    def get_mount_points(self):
        return self.mount_points

    def get(self, name):
        matching = [i for i in filter(lambda x: x.name == name, self.mount_points) ]
        if len(matching) == 0:
            return None
        return matching[0]



def execute(context, command, arg):
    if command == "list":
        available = context.get_mount_points()
        for i in available:
            print(f"{i}")
    elif command == "mount":
        mount = context.get(arg)
        if mount is None:
            print(f"{command}: '{arg}' could not be found")
            return
        if mount.ismounted():
            print(f"{command}: '{arg}' is already mounted")
            return
        mount.mount()
    elif command == "help":
        print("Available commands: list, mount, unmount")
    elif command == "unmount":
        mount = context.get(arg)
        if mount is None:
            print(f"{command}: '{arg}' could not be found")
            return
        if not mount.ismounted():
            print(f"{command}: '{arg}' is not mounted")
            return
        mount.unmount()
    else:
        print(f"Unknown command {command}")

def main(argv):
    o = SerialMounter()
    command = None
    arg = None

    if len(argv) == 1:
        mount_points = o.get_mount_points()
        while True:
            for i in range(len(mount_points)):
                print(f"{i} - {mount_points[i]}")
        
            try:
                selected = input("select> ")
            except KeyboardInterrupt:
                selected = 'q'

            if selected == 'q':
                sys.exit(0)
            if selected in [ 'r', '' ]:
                continue

            if int(selected) > len(mount_points) or int(selected) < 0:
                raise RuntimeError
        
            point = mount_points[selected]
            point.toggle()
        return

    if len(argv) >= 2:
        command = argv[1]

    if len(argv) >= 3:
        arg = argv[2]

    execute(o, command, arg)

if __name__ == "__main__":
    # execute only if run as a script
    main(sys.argv)
