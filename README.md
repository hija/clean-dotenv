[![build status](https://github.com/hija/clean-dotenv/actions/workflows/main.yml/badge.svg)](https://github.com/hija/clean-dotenv/actions/workflows/main.yml)
[![PyPI version](https://badge.fury.io/py/clean-dotenv.svg)](https://badge.fury.io/py/clean-dotenv)

clean-dotenv
======================

Automatically creates an `.env.example` which creates the same keys as your `.env` file, but without the values

## Why?
There are projects which make use of an `.env` file. An `.env` file contains environment variables which are used during runtime, such as API keys.
A typical `.env` file might look like this:

```bash
OPENAI_KEY="12345"
S3_BUCKET_NAME="testbucket"
```

An `.env` file should not be commited into a repo, since it can contain sensitive information[^1] (you should probably adding the `.env` file into your `.gitignore`). However, one needs to know which variables can be set in the `.env` file and as a result, a lot of projects (such as laravel), provide an `.env.example` file which is a template file. So you would copy the `.env.template`, rename it to `.env` and fill in the environment variables.

However, there is one issue with this approach: If one introduces a new environment variable, they need to remember to add it to the `.env.example` file. Unfortunately, if they forget this, it will not be noticed, since the program is using the `.env` file and not the `.env.example`. This pre-commit hook tries to mitigate this problem by creating an `.env.example` file automatically (based on your `.env` file), so the example `.env` file would become the following `.env.example`:

```bash
OPENAI_KEY=
S3_BUCKET_NAME=
```

[^1]: https://www.zdnet.com/article/botnets-have-been-silently-mass-scanning-the-internet-for-unsecured-env-files/
 
## Installation

```bash
pip install clean-dotenv
```


## Console scripts

Consult `clean-dotenv --help` for the full set of options.

Common options:

- `--root path`: Defines the root path in which to look for .env files. This is **not recursive**

## As a pre-commit hook

See [pre-commit](https://github.com/pre-commit/pre-commit) for instructions

Sample `.pre-commit-config.yaml`

```yaml
-   repo: https://github.com/hija/clean-dotenv
    rev: v0.0.5
    hooks:
    -   id: clean-dotenv
```

## What does it do?
The tool looks for `.env` files in all directories and creates a new, corresponding filename `.env.example` which is save to commit, since it contains all the keys from your `.env` file, but without its values.

As a result, you always have an up-to-date `.env.example` file. This shall help to reduce forgetting updating the `.env.example` files!

## Technical Background
Since a `.env` file is probably in the `.gitignore` file, we cannot rely on pre-commits [`files`-filter](https://pre-commit.com/#hooks-files). Instead, we tell pre-commit to run always. We then check for each subdirectory if an `.env` file exists. If it exists, we automatically create an `.env.example` file.

## Alternatives
The biggest alternative is to not use `.env` files at all[^2]. If you want to keep using `.env` files without using clean-dotenv you can use language specific tools, such as [dotenv-safe](https://github.com/rolodato/dotenv-safe) for node.

[^2]: https://dev.to/gregorygaines/stop-using-env-files-now-kp0

## Next Steps / Ideas
* Add an option to specify the `glob` pattern to increase the performance (e.g. you could specify to look for `dev/local.env` only)
