import os

EXCLUDE_DIRS = {"venv", "__pycache__", ".git", "node_modules"}
MAX_DEPTH = 2


def print_tree(dir_path, prefix="", depth=0):
    if depth > MAX_DEPTH:
        return
    entries = [e for e in os.listdir(dir_path) if e not in EXCLUDE_DIRS]
    entries.sort()
    for i, entry in enumerate(entries):
        path = os.path.join(dir_path, entry)
        connector = "└── " if i == len(entries) - 1 else "├── "
        print(prefix + connector + entry)
        if os.path.isdir(path):
            extension = "    " if i == len(entries) - 1 else "│   "
            print_tree(path, prefix + extension, depth + 1)


print_tree(".")
