import os
import subprocess
import sys


def get_current_freeze():
    """Gets the pip freeze output from the current active environment."""
    result = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_code=True, text=True)
    if result.returncode != 0:
        print("Error running pip freeze")
        sys.exit(1)
    return result.stdout.splitlines()


def merge_requirements(file_path="requirements.txt"):
    """Merges new packages into requirements.txt without altering existing ones."""
    existing_packages = {}

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()              
                if not line or line.startswith("#") or line.startswith("-e"):
                    continue
                if "==" in line:
                    pkg_name, _ = line.split("==", 1)
                    existing_packages[pkg_name.lower().replace("_", "-")] = line
                else:
                    existing_packages[line.lower()] = line

    current_freeze = get_current_freeze()
    added_count = 0

    for line in current_freeze:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-e"):
            continue
        if "==" in line:
            pkg_name, _ = line.split("==", 1)
            clean_name = pkg_name.lower().replace("_", "-")

            if clean_name not in existing_packages:
                existing_packages[clean_name] = line
                print(f"Detected new package: {line}")
                added_count += 1

    if added_count > 0:
        sorted_lines = [existing_packages[k] for k in sorted(existing_packages.keys())]
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted_lines) + "\n")
        print(f"Success! Added {added_count} new packages to {file_path}.")
    else:
        print("No new packages detected. Your requirements.txt is up to date.")


if __name__ == "__main__":
    merge_requirements()