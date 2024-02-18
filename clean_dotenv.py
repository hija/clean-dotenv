import glob
import os
import argparse
import dotenv.main


def clean_env(path_to_env: str):
    # Open the .env file and remove the sensitive data
    # We rely on python-dotenv to parse the file, since we do not want to write our own parser

    dotenv_file = dotenv.main.DotEnv(dotenv_path=path_to_env)

    # Create new filename for the .env file --> test.env becomes test.env.example
    path_to_example_file = path_to_env + ".example"

    # Write .example file
    with open(path_to_example_file, "w") as example_env_f:
        for key, _ in dotenv_file.dict().items():
            print(f"{key}=", file=example_env_f)


def clean_dotenv_files(path_to_root: str):
    # Find possible .env files
    for env_file in glob.iglob(
        pathname="**/*.env", root_dir=path_to_root, recursive=True
    ):

        # Clean .env files
        clean_env(env_file)


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
    clean_dotenv_files(args.root_path)


if __name__ == "__main__":
    raise SystemExit(main())
