import argparse
from pathlib import Path
import shutil

import argparse
from pathlib import Path
import shutil

def init():
    docs_path = Path("docs")
    dist_path = docs_path / "dist"
    src_path = docs_path / "src"
    contributing_file = src_path / "contributing.md"
    static_src = Path("static")
    templates_src = Path("templates")
    static_dst = docs_path / "static"
    templates_dst = docs_path / "templates"
    header_config = Path("header_config.yaml")
    header_config_dst = docs_path / "header_config.yaml"

    if not docs_path.exists():
        # Create folder structure
        dist_path.mkdir(parents=True)
        src_path.mkdir(parents=True)
        contributing_file.touch()

        # Copy static/ and templates/
        if static_src.exists():
            shutil.copytree(static_src, static_dst)
        else:
            print("Warning: 'static/' folder not found.")

        if templates_src.exists():
            shutil.copytree(templates_src, templates_dst)
        else:
            print("Warning: 'templates/' folder not found.")

        # Copy header_config.yaml
        if header_config.exists():
            shutil.copy(header_config, header_config_dst)
        else:
            print("Warning: 'header_config.yaml' not found.")

        print("Created 'docs' structure and copied all necessary files.")
    else:
        print("'docs' folder already exists.")


def run():
    print("Run command executed. (You can add functionality later.)")

def main():
    parser = argparse.ArgumentParser(description="Simple CLI tool with init and run.")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init", help="Create 'docs' folder structure.")
    subparsers.add_parser("run", help="Run the tool.")

    args = parser.parse_args()

    if args.command == "init":
        init()
    elif args.command == "run":
        run()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
