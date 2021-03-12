# smount - A mountpoint Manager

## Summary

This tools aims at simplifying and gathering "shortcuts" to quickly
mount/unmount remote file systems. This is a very simple project for now, there
is no support of udev rules or anything "complex", just the base to support my
use case.

There is no particular requirement, using python 3.8 or greature should be
sufficient.

## Usage

### Configuration

Write a file as:
  - /etc/smount
  - ~/.local/smount
  - ~/.smount

Or create directories instead, and setup multiple files inside.

Configuration files follow YAML syntax; for example:

```yaml
mount_types:
    - veracrypt:
        mount: "veracrypt --text -mro $src $target"
        umount: "veracrypt -d $target"
    - ssh:
        mount: "sshfs login@my_remote.lan:$src $target"
        umount: "umount $target"

mounts:
    - secrets:
        type: "veracrypt"
        src: "~/Documents/encrypted*.hc"
        expand: "last-ctime"
        target: "/media/secret"
    - public:
        type: "ssh"
        src: "/public"
        target: "/media/public"
```

Variables that can be used:
- $src
- $target
- $login
- $uid
- $gid

Available expansions:
- last-ctime : last file in the expanded list
- last-alpha : last file in alpha order in expanded list

Mount destinations should exist and have right permissions on it.

### Running as interactive

```bash
./smount-bin
```

### Running as cli

```bash
./smount-bin help
```

## Improvement list

- [ ] Add a logger with several verbosity levels
- [ ] Support udev for local disks matching
- [ ] Build a curses interface, for fun and profit
- [ ] Add a `variables` set in configuration for user defined variables
- [X] Propose automatically defined variables, as hostname, user login, ...
- [X] Propose wildcards in source mountpoints to automatically select a file
      without full name


