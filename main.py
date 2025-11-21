import os
import sys
import json
import tarfile
import tempfile
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
import argparse

from file_selector import FileSelector


class BackupTool:
    def __init__(self, config_path: str, remote_url: str):
        self.config_path = config_path
        self.remote_url = remote_url
        self.project_root = Path(config_path).parent.resolve()
        
        self.config = {}
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)
        
        self.file_selector = FileSelector(os.path.dirname(config_path))
        self.file_selector.add_include_patterns(self.config.get('include_patterns', []))
        self.file_selector.add_exclude_patterns(self.config.get('exclude_patterns', []))
    
    def create_tar_archive(self):
        timestamp = datetime.now().strftime(self.config.get('backup_name', '%Y-%m-%d-%H%M%S'))
        backup_name = f"{timestamp}.tar.gz"
        temp_archive = Path(tempfile.gettempdir()) / backup_name
        
        try:
            with tarfile.open(temp_archive, 'w:gz') as tar:
                for file_path in self.file_selector.get_files():
                    try:
                        arcname = file_path.relative_to(self.project_root)
                        tar.add(file_path, arcname=arcname)
                        print(f"Adding: {arcname}")
                    except ValueError as e:
                        print(f"Warning: Failed to add {file_path}: {e}")
                    except Exception as e:
                        print(f"Warning: Failed to add {file_path}: {e}")
            
            print(f"Archive created: {temp_archive}")
            return temp_archive
        except Exception as e:
            print(f"Failed to create archive: {e}")
            return None
    
    def _local_backup(self, archive_path: Path):
        local_folder = self.config.get('local_backup_folder')
        if not local_folder:
            print("Local backup folder not configured, skipping local backup")
            return True
        
        local_path = self.project_root / local_folder
        local_path.mkdir(parents=True, exist_ok=True)
        dest_path = local_path / archive_path.name
        
        try:
            shutil.copy2(archive_path, dest_path)
            print(f"Local backup completed: {dest_path}")
            return True
        except Exception as e:
            print(f"Local backup failed: {e}")
            return False
    
    def _remote_backup(self, archive_path: Path):
        remote_folder = self.config.get('remote_backup_folder')
        if not remote_folder or not self.remote_url:
            print("Remote backup folder or URL not configured, skipping remote backup")
            return True
        
        if not shutil.which('cadaver'):
            print("Warning: 'cadaver' command not found, skipping remote backup")
            return False

        script_file = None
        try:
            script_content = f"open {self.remote_url}\nmkdir {remote_folder}\ncd {remote_folder}\nput {archive_path}\nquit"
            script_file = tempfile.NamedTemporaryFile(mode='w', suffix='.cadaver', delete=False)
            script_file.write(script_content)
            script_file.close()
            
            print("Starting remote backup...")
            result = subprocess.run(['cadaver', '-r', script_file.name], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("Remote backup completed")
                return True
            else:
                print(f"Remote backup failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Remote backup error: {e}")
            return False
        finally:
            if script_file and os.path.exists(script_file.name):
                os.unlink(script_file.name)
    
    def backup(self):
        archive_path = self.create_tar_archive()
        if not archive_path:
            return
        
        self._local_backup(archive_path)
        self._remote_backup(archive_path)
        
        if archive_path.exists():
            archive_path.unlink()
            print(f"Temporary archive deleted: {archive_path}")


def main():
    parser = argparse.ArgumentParser(description='Backup Tool')
    parser.add_argument('-c', '--config', dest='config_path', required=True, help='Config file path')
    parser.add_argument('-r', '--remote', dest='remote_url', help='WebDAV remote URL')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.config_path):
        print(f"Error: Config file not found: {args.config_path}")
        sys.exit(1)
    
    BackupTool(args.config_path, args.remote_url).backup()


if __name__ == "__main__":
    main()
