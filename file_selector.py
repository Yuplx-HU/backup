import fnmatch
from pathlib import Path
from typing import List, Set


class FileSelector:
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir).resolve()
        self.include_patterns = []
        self.exclude_patterns = []
    
    def add_include_patterns(self, patterns: list[str]) -> None:
        self.include_patterns.extend(patterns)
    
    def add_exclude_patterns(self, patterns: list[str]) -> None:
        self.exclude_patterns.extend(patterns)
    
    def _get_all_file_paths(self, folder_path: Path) -> Set[Path]:
        files = set()
        stack = [folder_path]
        
        while stack:
            current = stack.pop()
            try:
                for item in current.iterdir():
                    if item.is_file():
                        files.add(item.resolve())
                    elif item.is_dir():
                        stack.append(item)
            except (PermissionError, OSError):
                continue
                
        return files
    
    def _match_pattern(self, path: Path, pattern: str) -> bool:
        try:
            relative_path = path.relative_to(self.base_dir)
            relative_path_str = str(relative_path).replace("\\", "/")
            return fnmatch.fnmatch(relative_path_str, pattern)
        except ValueError:
            return False
    
    def _apply_patterns(self, files: Set[Path], patterns: List[str], include: bool) -> Set[Path]:
        if not patterns:
            return files if include else set()
        
        result = set()
        for pattern in patterns:
            matched_files = {f for f in files if self._match_pattern(f, pattern)}
            if include:
                result.update(matched_files)
            else:
                result = files - matched_files
            files = result if include else files - matched_files
        
        return result
    
    def get_files(self) -> List[Path]:
        all_files = self._get_all_file_paths(self.base_dir)
        
        if self.include_patterns:
            included_files = self._apply_patterns(all_files, self.include_patterns, include=True)
        else:
            included_files = all_files
        
        if self.exclude_patterns:
            final_files = self._apply_patterns(included_files, self.exclude_patterns, include=False)
        else:
            final_files = included_files
        
        return sorted(final_files)


if __name__ == "__main__":
    selector = FileSelector()
    selector.add_exclude_patterns([".git/**"])
    print(selector.get_files())
