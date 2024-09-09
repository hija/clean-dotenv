import os
import argparse
from collections.abc import Iterator
import clean_dotenv._parser as DotEnvParser


def _clean_env(path_to_env: str, values_to_keep: list[str] = []):
    # Open the .env file and remove the sensitive data
    # We rely on python-dotenv to parse the file, since we do not want to write our own parser
    dotenv_elements = DotEnvParser.parse_stream(open(path_to_env))

    # Create new filename for the .env file --> test.env becomes test.env.example
    path_to_example_file = path_to_env + ".example"

    # Write .example file
    with open(path_to_example_file, "w") as example_env_f:
        # We now iterate through the original .env file and write everything except for the value into the new file
        for i, dotenv_element in enumerate(dotenv_elements):
            if dotenv_element.multiline_whitespace:
                print(dotenv_element.multiline_whitespace, end="", file=example_env_f)
            if dotenv_element.export:  # e.g. export AWS_KEY=...
                print(dotenv_element.export, end="", file=example_env_f)
            if dotenv_element.key:
                print(
                    (
                        f"{dotenv_element.key}={dotenv_element.separator}{dotenv_element.value}{dotenv_element.separator}"
                        if dotenv_element.key in values_to_keep
                        else f"{dotenv_element.key}={dotenv_element.separator}{dotenv_element.separator}"
                    ),
                    end="",
                    file=example_env_f,
                )
            if dotenv_element.comment:
                print(dotenv_element.comment, end="", file=example_env_f)
            if dotenv_element.end_of_line:
                print(dotenv_element.end_of_line, end="", file=example_env_f)


def _find_dotenv_files(path_to_root: str) -> Iterator[str]:
    # Finds and yields .env files in the path_to_root
    for entry in os.scandir(path_to_root):
        if entry.name.endswith(".env") and entry.is_file():
            # Create a cleaned .env.example file for the found .env file
            yield entry.path


def _main(path_to_root: str, values_to_keep: list[str] = []):
    # Find possible .env files
    for dotenv_file in _find_dotenv_files(path_to_root):
        # Clean dotenv file
        _clean_env(path_to_env=dotenv_file, values_to_keep=values_to_keep)


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
    parser.add_argument(
        "-k",
        "--keep",
        nargs="*",
        help="Variables which shall not be cleaned by clean-dotenv. Separate values by space.",
        default=[],
    )

    args = parser.parse_args()
    _main(path_to_root=args.root_path, values_to_keep=args.keep)


if __name__ == "__main__":
    raise SystemExit(main())
