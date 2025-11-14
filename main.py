import os
import sys
import json
import tarfile
import tempfile
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
import fnmatch
import argparse


class BackupConfig:
    def __init__(self, config_path):
        self.config_path = Path(config_path)
        self.project_root = self.config_path.parent
        self.data = {}
        self.load_config()
    
    def load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            print(f"错误: 配置文件 {self.config_path} 不存在")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"错误: 配置文件格式错误 - {e}")
            sys.exit(1)
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def generate_backup_name(self):
        name_template = self.get('backup_name', '%Y-%m-%d-%s')
        now = datetime.now()
        
        backup_name = now.strftime(name_template)
        return backup_name + '.tar.gz'


class BackupTool:
    def __init__(self, remote_url, config_path):
        self.remote_url = remote_url
        self.config = BackupConfig(config_path)
        self.files_to_backup = set()
    
    def should_exclude(self, path):
        try:
            rel_path = str(path.relative_to(self.config.project_root))
        except ValueError:
            return False
        
        if path.is_file():
            for pattern in self.config.get('exclude_files', []):
                if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(path.name, pattern):
                    return True
        
        if path.is_dir():
            for pattern in self.config.get('exclude_folders', []):
                rel_path_obj = Path(rel_path)
                pattern_path = Path(pattern)
                
                if (rel_path_obj == pattern_path or 
                    pattern_path in rel_path_obj.parents or
                    rel_path_obj in pattern_path.parents):
                    return True
                
                if fnmatch.fnmatch(rel_path, pattern):
                    return True
        
        return False
    
    def is_valid_file(self, path):
        return path.is_file() and not path.is_symlink()
    
    def collect_files(self):
        print("正在收集文件...")
        
        for file_pattern in self.config.get('include_files', []):
            if file_pattern:
                try:
                    for file_path in self.config.project_root.glob(file_pattern):
                        if self.is_valid_file(file_path) and not self.should_exclude(file_path):
                            self.files_to_backup.add(file_path)
                except Exception as e:
                    print(f"警告: 处理文件模式 '{file_pattern}' 时出错: {e}")
        
        for folder_pattern in self.config.get('include_folders', []):
            if not folder_pattern:
                continue
                
            if folder_pattern == '.':
                self.process_folder(self.config.project_root)
            else:
                try:
                    for folder_path in self.config.project_root.glob(folder_pattern):
                        if folder_path.is_dir():
                            self.process_folder(folder_path)
                except Exception as e:
                    print(f"警告: 处理文件夹模式 '{folder_pattern}' 时出错: {e}")
        
        print(f"找到 {len(self.files_to_backup)} 个文件需要备份")
    
    def process_folder(self, folder_path):
        try:
            for item in folder_path.iterdir():
                if item.is_dir() and not self.should_exclude(item):
                    self.process_folder(item)
                elif self.is_valid_file(item) and not self.should_exclude(item):
                    self.files_to_backup.add(item)
        except PermissionError:
            print(f"警告: 无权限访问文件夹 {folder_path}")
        except Exception as e:
            print(f"警告: 处理文件夹 {folder_path} 时出错: {e}")
    
    def create_tar_archive(self):
        backup_name = self.config.generate_backup_name()
        temp_archive = Path(tempfile.gettempdir()) / backup_name
        
        print(f"正在创建归档文件: {backup_name}")
        
        try:
            with tarfile.open(temp_archive, 'w:gz') as tar:
                for file_path in sorted(self.files_to_backup):
                    try:
                        arcname = file_path.relative_to(self.config.project_root)
                        tar.add(file_path, arcname=arcname)
                        print(f"  添加: {arcname}")
                    except Exception as e:
                        print(f"警告: 添加文件 {file_path} 时出错: {e}")
            
            print(f"归档文件创建成功: {temp_archive}")
            return temp_archive
        except Exception as e:
            print(f"创建归档文件时出错: {e}")
            return None
    
    def local_backup(self, archive_path):
        local_folder = self.config.get('local_backup_folder')
        if not local_folder:
            return True
        
        local_path = self.config.project_root / local_folder
        local_path.mkdir(parents=True, exist_ok=True)
        dest_path = local_path / archive_path.name
        
        try:
            shutil.copy2(archive_path, dest_path)
            print(f"本地备份完成: {dest_path}")
            return True
        except Exception as e:
            print(f"本地备份失败: {e}")
            return False
    
    def remote_backup(self, archive_path):
        remote_folder = self.config.get('remote_backup_folder')
        if not remote_folder or not self.remote_url:
            return True
        
        if not shutil.which('cadaver'):
            print("警告: cadaver工具未找到，跳过远程备份")
            return False

        try:
            script_content = f"open {self.remote_url}\nmkdir {remote_folder}\ncd {remote_folder}\nput {archive_path}\nquit"
            script_file = tempfile.NamedTemporaryFile(mode='w', suffix='.cadaver', delete=False)
            script_file.write(script_content)
            script_file.close()
            
            print("正在上传到远程服务器...")
            result = subprocess.run(['cadaver', '-r', script_file.name])
            
            if result.returncode == 0:
                print("远程备份完成")
                return True
            else:
                print(f"远程备份失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"远程备份出错: {e}")
            return False
        finally:
            if os.path.exists(script_file.name):
                os.unlink(script_file.name)
    
    def backup(self):
        print(f"开始备份项目: {self.config.project_root}")
        
        self.collect_files()
        
        if not self.files_to_backup:
            print("没有找到需要备份的文件")
            return
        
        archive_path = self.create_tar_archive()
        if not archive_path:
            return
        
        success = True
        local_enabled = bool(self.config.get('local_backup_folder'))
        remote_enabled = bool(self.config.get('remote_backup_folder'))
        
        if not local_enabled and not remote_enabled:
            print("警告: 未配置本地或远程备份路径，归档文件将保存在临时目录")
            print(f"临时文件位置: {archive_path}")
            return
        
        if local_enabled:
            if not self.local_backup(archive_path):
                success = False
        
        if remote_enabled and success:
            if not self.remote_backup(archive_path):
                success = False
        
        if success:
            print("备份完成!")
        else:
            print("备份过程中出现错误")
        
        if not (success and local_enabled and not remote_enabled):
            try:
                if archive_path.exists():
                    archive_path.unlink()
                    print("已清理临时文件")
            except Exception as e:
                print(f"清理临时文件时出错: {e}")


def main():
    parser = argparse.ArgumentParser(description='备份工具')
    parser.add_argument('-c', '--config', dest='config_path', help='配置文件路径')
    parser.add_argument('-r', '--remote', dest='remote_url', help='WebDAV服务器地址')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.config_path):
        print(f"错误: 配置文件 {args.config_path} 不存在")
        sys.exit(1)
    
    BackupTool(args.remote_url, args.config_path).backup()


if __name__ == "__main__":
    main()
