[![PyPI version](https://badge.fury.io/py/clean-dotenv.svg)](https://badge.fury.io/py/clean-dotenv)

clean-dotenv
======================

Automatically creates an .env.example which creates the same keys as your .env file, but without the values


## Installation

```bash
pip install clean-dotenv
```


## Console scripts

Consult `clean-dotenv --help` for the full set of options.

Common options:

- `--root path`: Defines the root path in which to look for .env files

## As a pre-commit hook

See [pre-commit](https://github.com/pre-commit/pre-commit) for instructions

Sample `.pre-commit-config.yaml`

```yaml
-   repo: https://github.com/hija/clean-dotenv
    rev: v0.0.2
    hooks:
    -   id: clean-dotenv
```

## What does it do?
The tool looks for `.env` files in all directories and creates a new, corresponding filename `.env.example` which is save to commit, since it contains all the keys from your `.env` file, but without its values.

As a result, you always have an up-to-date `.env.example` file. This shall help to reduce forgetting updating the `.env.example` files!