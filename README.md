# Backup Tool

A simple and easy-to-use file backup tool that supports local and remote backups.

## Features

- Configuration file-based backup settings
- Flexible include/exclude rules
- Local backup to specified folders
- Remote backup to WebDAV servers (via cadaver)
- Automatic packaging as tar.gz compressed files

## Dependencies

Only configure the following if remote backup is needed

### Root Environment
```bash
sudo apt-get install cadaver
```

### Non-Root Environment

In non-root environments, download the corresponding version of the deb package from https://pkgs.org/ and install:
```bash
wget http://ftp.de.debian.org/debian/pool/main/c/cadaver/cadaver_xxx.deb

dpkg-deb -x cadaver_xxx.deb cavader
```

Configure `~/.bashrc` environment:
```txt
# cadaver
export CADAVER_PATH="/path/to/cadaver/usr/bin"
export PATH="$CADAVER_PATH:$PATH"
```

Configure `~/.netrc` environment:
```txt
machine webdav-url
login example@mail.com
password thirdparty-application-password
```

Enable environment:
```bash
source ~/.bashrc
```

## Usage

### 1. Create Configuration File

Create a `.backup` file in the project directory that needs to be backed up:

```json
{
    "include_patterns": [],
    "exclude_patterns": [],

    "backup_name": "",

    "local_backup_folder": "",
    "remote_backup_folder": ""
}
```

Example:
```json
{
    "exclude_patterns": [
        ".env",
        ".git/*",
        "backup/*",
        "__pycache__/*"
    ],

    "local_backup_folder": "backup/",
    "remote_backup_folder": "projs/backup/"
}
```

No `include_patterns` means to include all the files and folders in the work space.

No `backup_name` means to use `%Y-%m-%d-%H%M%S`.


### 2. Run Backup

```bash
# Without remote backup
python main.py -c /path/to/.backup

# With remote backup
python main.py -c /path/to/.backup -r webdav-url
```

## Configuration Explanation

- **include_patterns**: Folders and files to include
- **exclude_patterns**: Folders and files to exclude
- **backup_name**: Backup file naming format (using strftime format)
- **local_backup_folder**: Local backup path (relative to project root)
- **remote_backup_folder**: Remote backup path (WebDAV server path)
