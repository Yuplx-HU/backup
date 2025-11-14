# 备份工具

一个简单易用的文件备份工具，支持本地和远程备份。


## 功能特性

- 基于配置文件进行备份设置
- 支持灵活的包含/排除规则
- 本地备份到指定文件夹
- 远程备份到WebDAV服务器（通过cadaver）
- 自动打包为tar.gz压缩文件


## 安装依赖

只有需要远程保存备份才进行以下配置


### root环境
```bash
sudo apt-get install cadaver
```


### 非root环境

非root环境下要从[pkgs](https://pkgs.org/)上下载对应版本的deb包并安装:
```bash
wget ttp://ftp.de.debian.org/debian/pool/main/c/cadaver/cadaver_xxx.deb

dpkg-deb -x cadaver_xxx.deb cavader
```

配置`~/.bashrc`环境:
```txt
# cadaver
export CADAVER_PATH="/path/to/cadaver/usr/bin"
export PATH="$CADAVER_PATH:$PATH"
```

在用户目录下配置`~/.netrc`, 这里使用的是坚果云, 密码需要在坚果云中授权第三方应用后获得:
```txt
machine webdav-url
login example@mail.com
password thirdparty-application-passwprd
```

启用环境:
```bash
source ~/.bashrc
```


## 使用方法


### 1. 创建配置文件

在需要备份的项目目录下创建`.backup`文件：

```json
{
    "include_files": [],
    "include_folders": [],
    "exclude_files": [],
    
    "exclude_folders": [],

    "backup_name": "",

    "local_backup_folder": "",
    "remote_backup_folder": ""
}
```

案例:
```json
{
    "include_files": [],
    "include_folders": [
        "."
    ],
    "exclude_files": [
        ".env"
    ],
    
    "exclude_folders": [
        ".git",
        "backup",
        "__pycache__"
    ],

    "backup_name": "%Y-%m-%d-%s",

    "local_backup_folder": "backup",
    "remote_backup_folder": "projs/backup"
}
```

### 2. 运行备份

```bash
# 不进行远程备份
python backup.py -c /path/to/project/.backup

# 进行远程备份
python backup.py -c /path/to/project/.backup -r webdav-url
```

## 配置说明

- **include_files**: 要包含的特定文件（支持通配符）
- **include_folders**: 要包含的文件夹
- **exclude_files**: 要排除的文件
- **exclude_folders**: 要排除的文件夹
- **backup_name**: 备份文件命名格式（使用strftime格式）
- **local_backup_folder**: 本地备份路径（基于项目根目录）
- **remote_backup_folder**: 远程备份路径（WebDAV服务器路径）
