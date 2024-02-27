import os
import argparse
from typing import Iterator
import dotenv.main


def _clean_env(path_to_env: str):
    # Open the .env file and remove the sensitive data
    # We rely on python-dotenv to parse the file, since we do not want to write our own parser

    dotenv_file = dotenv.main.DotEnv(dotenv_path=path_to_env)

    # Create new filename for the .env file --> test.env becomes test.env.example
    path_to_example_file = path_to_env + ".example"

    # Write .example file
    with open(path_to_example_file, "w") as example_env_f:
        for key, _ in dotenv_file.dict().items():
            print(f"{key}=", file=example_env_f)


def _find_dotenv_files(path_to_root: str) -> Iterator[str]:
    # Finds and yields .env files in the path_to_root
    for entry in os.scandir(path_to_root):
        if entry.name.endswith(".env") and entry.is_file():
            # Create a cleaned .env.example file for the found .env file
            yield entry.path


def _main(path_to_root: str):
    # Find possible .env files
    for dotenv_file in _find_dotenv_files(path_to_root):
        # Clean dotenv file
        _clean_env(dotenv_file)


def main():
    parser = argparse.ArgumentParser(
        description="Automatically creates an .env.example which creates the same keys as your .env file, but without the values"
    )
    parser.add_argument(
        "--root_path",
        type=str,
        help="Root path in which .env files shall be looked for",
        default=os.getcwd(),
    )
    args = parser.parse_args()
    _main(args.root_path)


if __name__ == "__main__":
    raise SystemExit(main())
