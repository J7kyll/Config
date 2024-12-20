import tarfile
import os
import sys


class VirtualFileSystem:
    def __init__(self, tar_path):
        self.tar_path = tar_path
        self.tree = {}
        self.current_dir = "/"
        self._load_filesystem()

    def _load_filesystem(self):
        with tarfile.open(self.tar_path, 'r') as tar:
            for member in tar.getmembers():
                path_parts = member.name.strip("/").split("/")
                current = self.tree
                for part in path_parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                if member.isdir():
                    current[path_parts[-1]] = {}
                else:
                    current[path_parts[-1]] = None  # Файл

    def ls(self):
        current = self._navigate_to(self.current_dir)
        if isinstance(current, dict):
            return sorted(f"{k}/" if isinstance(v, dict) else k for k, v in current.items())
        raise ValueError("Current path is not a directory")

    def cd(self, path):
        new_dir = self._resolve_path(path)
        if isinstance(self._navigate_to(new_dir), dict):
            self.current_dir = new_dir
        else:
            raise ValueError(f"{path} is not a directory")

    def pwd(self):
        return self.current_dir

    def _navigate_to(self, path):
        path_parts = [p for p in path.strip("/").split("/") if p]
        current = self.tree
        for part in path_parts:
            if part == "..":
                current = self.tree  # Для упрощения
            elif part in current:
                current = current[part]
            else:
                raise ValueError(f"Path {path} does not exist")
        return current

    def _resolve_path(self, path):
        if path.startswith("/"):
            return path.rstrip("/") or "/"
        if path == "..":
            return os.path.dirname(self.current_dir.rstrip("/")) or "/"
        return os.path.normpath(os.path.join(self.current_dir, path))


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser(description="UNIX-like shell emulator")
    parser.add_argument("--user", required=True, help="Username for the shell prompt")
    parser.add_argument("--fs", required=True, help="Path to the virtual filesystem tar archive")
    parser.add_argument("--script", required=False, help="Path to the startup script")
    return parser.parse_args()


def execute_script(script_path, user, vfs):
    try:
        with open(script_path, "r") as script:
            for line in script:
                command = line.strip()
                if not command or command.startswith("#"):
                    continue
                print(f"{user}@emulator:{vfs.pwd()}$ {command}")
                process_command(command, user, vfs)
    except FileNotFoundError:
        print(f"Error: Script file '{script_path}' not found.")
    except Exception as e:
        print(f"Error while executing script: {e}")


def process_command(command, user, vfs):
    try:
        if command == "exit":
            print("Goodbye!")
            sys.exit(0)
        elif command == "ls":
            print("\n".join(vfs.ls()))
        elif command.startswith("cd"):
            parts = command.split()
            if len(parts) < 2:
                print("Usage: cd <directory>")
            else:
                vfs.cd(parts[1])
        elif command.startswith("echo"):
            print(" ".join(command.split()[1:]))
        elif command == "who":
            print(user)
        elif command == "pwd":
            print(vfs.pwd())
        else:
            print(f"Unknown command: {command}")
    except Exception as e:
        print(f"Error: {e}")


def run_shell(user, fs, script=None):
    vfs = VirtualFileSystem(fs)

    if script:
        execute_script(script, user, vfs)

    while True:
        command = input(f"{user}@emulator:{vfs.pwd()}$ ").strip()
        process_command(command, user, vfs)


if __name__ == "__main__":
    args = parse_arguments()
    run_shell(args.user, args.fs, args.script)
