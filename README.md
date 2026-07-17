# smount - A mountpoint Manager

## Summary

This tools aims at simplifying and gathering "shortcuts" to quickly
mount/unmount remote file systems. This is a very simple project for now, there
is no support of udev rules or anything "complex", just the base to support my
use case.

There is no particular requirement, using python 3.8 or greater should be
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
# Global variables section
variables:
    my_remote_host: "my_remote.lan"
    backup_folder: "prompt:Enter backup subfolder name: "

mount_types:
    veracrypt:
      mount: "veracrypt --text -mro $src $target"
      umount: "veracrypt -d $target"
    ssh:
      mount: "sshfs login@$my_remote_host:$src $target"
      umount: "umount $target"

mounts:
    secrets:
      type: "veracrypt"
      src: "~/Documents/encrypted*.hc"
      expand: "last-ctime"
      target: "/media/secret"
    public:
      type: "ssh"
      src: "/public"
      target: "/media/$backup_folder"
      # Local variables (override global variables)
      variables:
          my_remote_host: "alt_remote.lan"
```

### Variables
`smount` supports both built-in and user-defined variables:

#### Built-in variables (automatically defined):
- `$src` : Source path
- `$target` : Target path
- `$login` : OS login user
- `$uid` : User ID
- `$gid` : Group ID

#### User-defined variables:
Define variables under the `variables:` dictionary, either globally or per-mountpoint. Local variables override global ones.
- **Constant Variables**: e.g., `my_remote_host: "my_remote.lan"`
- **Prompted Variables**: If the value is `"prompt"` or starts with `"prompt:"`, `smount` will dynamically prompt the user for input when the mount is requested.
  - e.g., `backup_folder: "prompt"` will prompt with `Enter value for backup_folder: `
  - e.g., `backup_folder: "prompt:Enter subfolder: "` will prompt with `Enter subfolder: `
  - When prompting for variables that look like paths (contain keywords like `path`, `file`, `dir`, `folder`, `src`, `target`), standard tab-based filename autocompletion is enabled.
  - Prompt values are cached in memory for subsequent operations (like checking status or unmounting).

### Expansions
Available expansions:
- `last-ctime` : last file in the expanded list
- `last-alpha` : last file in alpha order in expanded list

Mount destinations should exist and have right permissions on it.

### Commands

#### Interactive Mode (Readline-enabled)
```bash
./smount
```
Starts a terminal menu. Features:
- Tab-completion of commands (`q`, `quit`, `r`, `refresh`), mountpoint indexes, and names.
- Navigational history using Up/Down arrow keys.
- Quick navigation by index or by name.

#### Curses TUI Mode
```bash
./smount tui
```
Starts a full curses terminal user interface:
- **Up/Down Arrows**: Navigate through mountpoints
- **Enter**: Toggle mount/unmount the selected mountpoint
- **R**: Refresh configuration files
- **Q**: Quit
- Displays green indicators (🟢) for mounted systems and red indicators (🔴) for unmounted ones.
- Highlights unselected lines (green/red) and selected lines with a reverse-video bar on color-capable terminals.

#### CLI Command Mode
```bash
./smount mount <name>
./smount unmount <name>
./smount list
./smount help
```

### Logging & Verbosity
You can control the logging output via command-line options:
- Default: `INFO` level (reports main operations, e.g. success/failure).
- `-v` or `--verbose`: `DEBUG` level (shows executed shell commands, variable expansions, and loaded configurations).
- `-q` or `--quiet`: `ERROR` level (suppresses status logs, only shows critical exceptions and errors).

Example:
```bash
./smount -v mount secrets
```

## Screenshot

![Screenshot](https://github.com/lqp1/smount/blob/main/doc/screenshot.png?raw=true)

## Roadmap & Features

### Implemented Features
- [X] Standard Python logging interface with `-v`/`--verbose` and `-q`/`--quiet` levels.
- [X] Curses TUI mode for navigating and toggling mounts.
- [X] Interactive terminal menu with `readline` (arrow history & Tab completion).
- [X] Global and local user-defined `variables`, supporting on-demand user prompting and caching.
- [X] Automatically defined variables (hostname, login user, uid, gid).
- [X] Wildcard glob source matching and expansions (`last-ctime`, `last-alpha`).

### Future Roadmap
- [ ] Support udev for local disks matching


